from dataclasses import dataclass


@dataclass
class Student:
    pass


@dataclass
class Speciality:
    code: str
    name: str
    page_id: str
    max_places: int | None = None
    strudents: list[Student] | None = None
