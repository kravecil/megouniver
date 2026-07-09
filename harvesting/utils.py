from urllib.parse import parse_qs, urlparse

import pandas as pd

from harvesting.models import Speciality


def get_page_id_from_url(url: str) -> str | None:
    parsed = urlparse(url)
    qs = parse_qs(parsed.fragment.lstrip("/?"))
    page_id_values = qs.get("id", [None])[0]

    return page_id_values


def specialities_to_flat_df(specialities: list[Speciality]) -> pd.DataFrame:
    records = []
    for spec in specialities:
        if not spec.students:
            records.append(
                {
                    "speciality_name": spec.name,
                    "speciality_max_places": spec.max_places,
                    "speciality_total_students": spec.total_students,
                    "student_number": None,
                    "student_code": None,
                    "student_priority": None,
                    "student_score": None,
                    "student_is_preferred": None,
                }
            )
            continue

        for student in spec.students:
            records.append(
                {
                    "speciality_name": spec.name,
                    "speciality_max_places": spec.max_places,
                    "speciality_total_students": spec.total_students,
                    "student_number": student.number,
                    "student_code": student.code,
                    "student_priority": student.priority,
                    "student_score": student.score,
                    "student_is_preferred": student.is_preferred,
                }
            )

    return pd.DataFrame(records)


def get_stats_text(df, student_code: int) -> str:
    rows = df[df["student_code"] == student_code].sort_values(by="student_priority")

    text = """Статистика по коду студента {}\n\n"""

    for _, row in rows.iterrows():
        text += "(Приоритет {}) {} (мест {}): {}/{}\n".format(
            row["student_priority"],
            row["speciality_name"],
            row["speciality_max_places"],
            row["student_number"],
            row["speciality_total_students"],
        )

    return text.format(student_code)
