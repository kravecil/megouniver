import asyncio
import logging
from dataclasses import dataclass
from typing import Self
from urllib.parse import urlencode, urljoin

from bs4 import BeautifulSoup

from harvesting.fetcher import Fetcher
from harvesting.interfaces import IHarvestable
from harvesting.models import Speciality, Student

logger = logging.getLogger(__name__)


@dataclass
class Option:
    value: int
    name: str
    ref: int | None = None


class Harvester(IHarvestable):
    name = "КФУ"

    _base_url: str = "https://abiturient.kpfu.ru/entrant/abit_entrant_originals_list"

    _p_level: int = 1  # Уровень образования: бакалавриат
    _p_inst: int = 0  # ВУЗ / Филиал: Казанский (Приволжский) федеральный университет
    _p_typeofstudy: int = 1  # Форма обучения: Очная

    def __init__(self, fetcher: Fetcher) -> None:
        self.fetcher = fetcher

    @classmethod
    async def create(cls) -> Self:
        fetcher = Fetcher()

        return cls(fetcher=fetcher)

    async def harvest(self) -> list[Speciality]:
        logger.info("Harvesting GUAP...")

        sem = asyncio.Semaphore(10)

        async with self.fetcher:
            pfaculties = await self._get_pfaculties()

            speciality_tasks = []
            for faculty in pfaculties:
                task = self._get_pspecialities(faculty, sem)
                speciality_tasks.append(task)

            pspecialities: list[list[Option]] = await asyncio.gather(*speciality_tasks)

            specialities = [
                Speciality(
                    name=option.name, ref=str(option.value), faculty_ref=str(option.ref)
                )
                for sublist in pspecialities
                for option in sublist
            ]

            gather_tasks = [self._gather_speciality_data(s, sem) for s in specialities]
            await asyncio.gather(*gather_tasks)

        return specialities

    def _build_url(
        self, p_faculty: int | None = None, p_speciality: int | None = None
    ) -> str:
        params = {
            "p_level": self._p_level,
            "p_inst": self._p_inst,
            "p_typeofstudy": self._p_typeofstudy,
        }

        if p_faculty is not None:
            params["p_faculty"] = p_faculty

        if p_speciality is not None:
            params["p_speciality"] = p_speciality

        query_string = urlencode(params)

        return urljoin(self._base_url, f"?{query_string}")

    async def _get_options(
        self, select_name: str, p_faculty: int | None = None
    ) -> list[Option]:
        url = self._build_url(p_faculty=p_faculty)

        html = await self.fetcher.fetch(url)

        soup = BeautifulSoup(html, "lxml")

        select = soup.find("select", attrs={"name": select_name})
        if not select:
            logger.warning(f"{select_name} <select> not found")
            return []

        options = []

        for option_el in select.find_all("option"):
            value = option_el.get("value")
            if not value:
                continue

            text = option_el.get_text(strip=True)

            try:
                code = int(str(value))
            except ValueError, TypeError:
                logger.debug(f"Skipping option with non-integer value: {value!r}")
                continue

            if text:
                option = Option(value=code, name=text)

                if p_faculty is not None:
                    option.ref = p_faculty

                options.append(option)

        return options

    async def _get_pfaculties(self) -> list[Option]:
        return await self._get_options("p_faculty")

    async def _get_pspecialities(
        self, faculty: Option, sem: asyncio.Semaphore
    ) -> list[Option]:
        async with sem:
            return await self._get_options("p_speciality", p_faculty=faculty.value)

    async def _gather_speciality_data(
        self, speciality: Speciality, sem: asyncio.Semaphore
    ) -> None:
        if speciality.ref is None or speciality.faculty_ref is None:
            logger.warning(f"Ref for {speciality} not found")
            return

        async with sem:
            url = self._build_url(
                p_faculty=int(speciality.faculty_ref), p_speciality=int(speciality.ref)
            )

            html = await self.fetcher.fetch(url)
            soup = BeautifulSoup(html, "lxml")

            max_places = 0
            p_tag = soup.find(
                "p"
            )  # TODO @me: искать конкретнее по string "План приема"
            if p_tag and p_tag.strong:
                try:
                    max_places = int(p_tag.strong.get_text(strip=True))
                except ValueError:
                    logger.warning(
                        f"Could not parse plan from <strong>: {p_tag.strong.get_text()!r}"
                    )

            total_students, students = await self._get_students(soup)

            speciality.max_places = max_places
            speciality.students = students
            speciality.total_students = total_students

    async def _get_students(self, soup: BeautifulSoup) -> tuple[int, list[Student]]:
        span = soup.find("span", string="на основные места в рамках контрольных цифр")

        if not span:
            logger.warning("Not found span")
            return 0, []

        h2 = span.find_parent("h2")
        if not h2:
            logger.warning("Not found span parent (h2)")
            return 0, []

        section = h2.find_parent("section")
        if not section:
            logger.warning("Not found span parent (section)")
            return 0, []

        tbody = section.find("tbody", class_="tablebig__body")
        if not tbody:
            logger.warning("Not found table body")
            return 0, []

        last_number = 0
        students = []
        for row in tbody.find_all("tr"):
            cells = row.find_all("td")

            number = int(cells[0].text.strip())
            last_number = number

            try:
                code = int(cells[1].text.strip())
                score = int(cells[-7].text.strip())
                priority = int(cells[-4].text.strip())
                is_preferred = False

                students.append(Student(number, code, priority, score, is_preferred))
            except ValueError:
                continue

        return last_number, students
