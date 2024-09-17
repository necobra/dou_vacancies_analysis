class Settings:
    DEFAULT_HEADERS = {
        "Host": "jobs.dou.ua",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36",
        "Referer": "https://jobs.dou.ua/",
        "Accept-Language": "en-US,en;q=0.9",
    }
    TAGS_TO_SEARCH = [
        "Backend",
        "Back-End",
        "Frontend",
        "Front-End",
        "Scarping",
        "Machine Learning",
    ]
    TECHNOLOGIES_TO_SEARCH = [
        "Django",
        "Flask",
        "Pytorch",
        "TensorFlow",
        "AWS",
        "Postgres",
        "Apache",
        "Redis",
        "C#",
        "Fastapi",
        "Flask",
        "SQLAlchemy",
        "Azure",
        "Playwright",
        "RabbitMQ",
        "Airflow",
    ]

    SEARCH_VALUE = "python"

    BASE_URL = "https://jobs.dou.ua/"
    SEARCH_URL = f"/vacancies/?search={SEARCH_VALUE}"
    LOAD_NEXT_URL = f"/vacancies/xhr-load/?search={SEARCH_VALUE}"

    FILE_NAME_TO_SAVE = "vacancies_data.csv"


settings = Settings()
