import logging
import sys

import pandas as pd

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

logger = logging.getLogger(__name__)


class Analyser:
    def __init__(self, df: pd.DataFrame, student_code: int) -> None:
        self.df = df
        self.student_code = student_code

    def analyse(self) -> tuple[str, str] | None:
        logger.info("Analysing...")

        specialities_df = self.df[
            [
                "speciality_code",
                "speciality_name",
                "speciality_page_id",
                "speciality_max_places",
            ]
        ].drop_duplicates()

        specialities = {}
        for row in specialities_df.itertuples():
            specialities[row.speciality_page_id] = {  # type: ignore[attr-defined]
                "code": row.speciality_code,  # type: ignore[attr-defined]
                "name": row.speciality_name,  # type: ignore[attr-defined]
                "max_places": row.speciality_max_places,  # type: ignore[attr-defined]
            }

        sorted_df = self.df.sort_values(
            ["student_number", "student_priority"]
        ).reset_index(drop=True)

        excluded_students: set[int] = set()
        for row in sorted_df.itertuples(index=False):
            speciality_page_id = row.speciality_page_id  # type: ignore[attr-defined]
            max_places = specialities[speciality_page_id]["max_places"]
            if max_places == 0:
                continue

            student_code = int(row.student_code)  # type: ignore[arg-type]
            if student_code == self.student_code:
                return (str(row.speciality_code), str(row.speciality_name))  # type: ignore[attr-defined]

            if student_code in excluded_students:
                continue

            specialities[speciality_page_id]["max_places"] = max_places - 1
            excluded_students.add(student_code)

        return None
