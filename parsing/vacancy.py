import dataclasses


@dataclasses.dataclass
class Vacancy:
    url: str
    is_remote: bool
    is_part_time: bool
    experience: str
    salary_min: int
    salary_max: int
    technologies: list[str]
    tags: list[str]
