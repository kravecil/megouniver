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
    name: str
    max_places: int | None = None
    students: list[Student] | None = None
