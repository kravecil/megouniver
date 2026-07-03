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
                    "speciality_code": spec.code,
                    "speciality_name": spec.name,
                    "speciality_page_id": spec.page_id,
                    "speciality_max_places": spec.max_places,
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
                    "speciality_code": spec.code,
                    "speciality_name": spec.name,
                    "speciality_page_id": spec.page_id,
                    "speciality_max_places": spec.max_places,
                    "student_number": student.number,
                    "student_code": student.code,
                    "student_priority": student.priority,
                    "student_score": student.score,
                    "student_is_preferred": student.is_preferred,
                }
            )

    return pd.DataFrame(records)
