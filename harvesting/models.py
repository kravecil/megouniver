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
    ref: str | None = None
    faculty_ref: str | None = None
    max_places: int | None = None
    total_students: int | None = None
    students: list[Student] | None = None
