import asyncio
import csv
import re
from pathlib import Path
from typing import List
from urllib.parse import urljoin

import aiohttp
import requests
from bs4 import BeautifulSoup
from tqdm.asyncio import tqdm_asyncio

from config import settings
from parsing.vacancy import Vacancy


def fetch_request(
    url: str, method: str, payload: dict = None, cookies: dict = None
) -> requests.request:
    response = requests.request(
        method,
        url,
        headers=settings.DEFAULT_HEADERS,
        data=payload,
        cookies=cookies,
    )
    return response


async def fetch_request_async(url: str, method: str) -> str:
    async with aiohttp.ClientSession() as session:
        async with session.request(
            method, url, headers=settings.DEFAULT_HEADERS
        ) as response:
            return await response.text()


def get_csrf_form_token(soup: BeautifulSoup):
    script_tags = soup.find_all("script")

    csrf_token = None
    for script in script_tags:
        match = re.search(r'window\.CSRF_TOKEN\s*=\s*"(.+?)"', str(script))
        if match:
            csrf_token = match.group(1)
            break

    if not csrf_token:
        raise ValueError

    return csrf_token


def get_all_vacancies_on_page(
    csrf_cookie_token: str, csrf_form_token: str
) -> List[BeautifulSoup]:
    additional_vacancies_soups = []
    cookies = {"csrftoken": csrf_cookie_token}
    payload = {"csrfmiddlewaretoken": csrf_form_token, "count": 20}
    while True:
        url = urljoin(settings.BASE_URL, settings.LOAD_NEXT_URL)
        response = fetch_request(
            url,
            "post",
            payload,
            cookies,
        )

        html_content = response.json()["html"]

        additional_vacancies_soups += [
            BeautifulSoup(html_content, "html.parser")
        ]

        if response.json()["last"]:
            break
        payload["count"] += 40

    return additional_vacancies_soups


def get_search_page_all_vacancies_soup() -> List[BeautifulSoup]:
    search_python_url = urljoin(settings.BASE_URL, settings.SEARCH_URL)
    search_page = fetch_request(search_python_url, "get")

    soup = BeautifulSoup(search_page.content, "html.parser")

    csrf_cookie_token = search_page.cookies.get_dict()["csrftoken"]
    csrf_form_token = get_csrf_form_token(soup)

    additional_vacancies_soups = get_all_vacancies_on_page(
        csrf_cookie_token, csrf_form_token
    )
    return [soup] + additional_vacancies_soups


async def parse_single_vacancy(url: str) -> Vacancy:
    response = await fetch_request_async(url, "get")
    soup = BeautifulSoup(response, "html.parser")
    soup = soup.select_one(".b-vacancy")

    is_remote = any(
        soup.find_all(string=lambda text: kw in text.lower())
        for kw in ["віддален", "remote"]
    )

    is_part_time = any(
        soup.find_all(string=lambda text: kw in text.lower())
        for kw in ["part time", "part-time", "погодинно"]
    )

    experience = ""
    for level in [
        "Trainee",
        "Стажер",
        "Junior",
        "Middle",
        "Senior",
        "Tech Lead",
        "Techlead",
        "Teamlead",
    ]:
        if soup.find_all(string=lambda text: level.lower() in text.lower()):
            experience = level
            break

    if experience in ["Tech Lead", "Techlead", "Teamlead"]:
        experience = "Tech Lead"
    elif experience in ["Trainee", "Стажер"]:
        experience = "Trainee"

    salary_min, salary_max = None, None
    salary_text = soup.select_one(".salary")
    if salary_text:
        salary_text = salary_text.text
        salary_numbers = [
            int(s.replace(",", "").strip())
            for s in re.findall(r"\d+", salary_text)
        ]
        if len(salary_numbers) == 2:
            salary_min, salary_max = salary_numbers
        elif len(salary_numbers) == 1:
            salary_min = salary_max = salary_numbers[0]

    technologies = [
        tech
        for tech in settings.TECHNOLOGIES_TO_SEARCH
        if soup.find_all(string=lambda text: tech.lower() in text.lower())
    ]

    tags = [
        tag
        for tag in settings.TAGS_TO_SEARCH
        if soup.find_all(string=lambda text: tag.lower() in text.lower())
    ]

    return Vacancy(
        url=url,
        is_remote=is_remote,
        is_part_time=is_part_time,
        experience=experience,
        salary_min=salary_min,
        salary_max=salary_max,
        technologies=technologies,
        tags=tags,
    )


def extract_vacancies_detailed_page_url(
    vacancys_soup: List[BeautifulSoup],
) -> list[str]:
    urls = []
    for soup in vacancys_soup:
        for vacancy in soup.select("a.vt") + soup.select('\\"vt\\"'):
            href = vacancy["href"].strip()
            urls.append(href)
    return urls


def write_to_csv(vacancies: tuple[Vacancy], output_csv_path: str) -> None:
    with open(
        Path("..", output_csv_path), "w", encoding="utf-8", newline=""
    ) as file:
        writer = csv.writer(file)
        writer.writerow(
            [
                "url",
                "experience",
                "salary_max",
                "salary_min",
                "is_remote",
                "is_part_time",
                "technologies",
                "tags",
            ]
        )
        for vacancy in vacancies:
            writer.writerow(
                [
                    vacancy.url,
                    vacancy.experience,
                    vacancy.salary_max,
                    vacancy.salary_min,
                    vacancy.is_remote,
                    vacancy.is_part_time,
                    vacancy.technologies,
                    vacancy.tags,
                ]
            )


async def get_all_vacancies(vacancies_urls: list[str]) -> tuple[Vacancy]:
    vacancies_tasks = [
        parse_single_vacancy(url)
        for url in tqdm_asyncio(vacancies_urls, desc="Parsing Vacancies")
    ]
    return await asyncio.gather(*vacancies_tasks)


async def main() -> None:
    soups = get_search_page_all_vacancies_soup()

    vacancies_urls = extract_vacancies_detailed_page_url(soups)

    vacancies = await get_all_vacancies(vacancies_urls)

    write_to_csv(vacancies, settings.FILE_NAME_TO_SAVE)


if __name__ == "__main__":
    asyncio.run(main())
