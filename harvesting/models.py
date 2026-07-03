from dataclasses import dataclass


@dataclass
class Student:
    number: int
    code: int
    priority: int
    score: int
    is_preferred: bool


@dataclass
class Speciality:
    code: str
    name: str
    page_id: str
    max_places: int | None = None
    students: list[Student] | None = None
