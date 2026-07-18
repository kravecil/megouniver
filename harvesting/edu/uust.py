import asyncio
import logging
from dataclasses import dataclass
from typing import Self

from bs4 import BeautifulSoup, Tag

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
    name = "УУНИТ"

    _base_url: str = "https://list.uust.ru"
    _specialities_uri: str = "/plan/2026/1/18/b/o"

    def __init__(self, fetcher: Fetcher) -> None:
        self.fetcher = fetcher

    @classmethod
    async def create(cls) -> Self:
        fetcher = Fetcher()

        return cls(fetcher=fetcher)

    async def harvest(self) -> list[Speciality]:
        logger.info("Harvesting GUAP...")

        sem = asyncio.Semaphore(60)

        async with self.fetcher:
            specialities = await self._get_specialities()

            speciality_tasks = [
                self._gather_speciality_data(speciality, sem)
                for speciality in specialities
            ]

            await asyncio.gather(*speciality_tasks)

        return [s for s in specialities if s.total_students]

    async def _get_specialities(self) -> list[Speciality]:
        logger.info("Fetching specialities list...")
        html = await self.fetcher.fetch(f"{self._base_url}{self._specialities_uri}")

        soup = BeautifulSoup(html, "lxml")

        tbody = soup.find("tbody")
        if not tbody:
            logger.warning("No tbody found")
            return []

        specialities: list[Speciality] = []
        speciality_name: str | None = None

        for row in tbody.find_all("tr"):
            _speciality_name = self._retreive_speciality_name(row)
            if _speciality_name is not None:
                speciality_name = _speciality_name
                continue

            _speciality_details = self._retreive_speciality_details(row)
            if _speciality_details:
                speciality_caption, max_places, ref = _speciality_details

                speciality = Speciality(
                    name=f"{speciality_name} ({speciality_caption})",
                    max_places=max_places,
                    ref=ref,
                )
                specialities.append(speciality)

        return specialities

    @staticmethod
    def _retreive_speciality_name(row: Tag) -> str | None:
        td = row.find("td")

        if not td:
            return

        td_style = td.attrs.get("style")
        if not td_style:
            return

        speciality_name = td.get_text(strip=True)

        return speciality_name

    @staticmethod
    def _retreive_speciality_details(row: Tag) -> tuple[str, int, str] | None:
        td = row.find("td", class_="text-left")
        if not td:
            return

        cells = row.find_all("td")

        caption_div = td.find("div", class_="table-structure-directions")
        if not caption_div:
            return

        speciality_caption = caption_div.get_text(strip=True)

        a_tag = cells[13].find("a")
        if not a_tag:
            return None

        ref = str(a_tag["href"])

        max_places = int(cells[9].text.strip())

        return speciality_caption, max_places, ref

    async def _gather_speciality_data(
        self, speciality: Speciality, sem: asyncio.Semaphore
    ) -> None:
        async with sem:
            html = await self.fetcher.fetch(f"{self._base_url}{speciality.ref}")

            soup = BeautifulSoup(html, "lxml")

            tbody = soup.find("tbody")
            if not tbody:
                logger.warning("No tbody")
                return

            students: list[Student] = []
            last_number = 0
            for row in tbody.find_all("tr"):
                cells = row.find_all("td")

                number = int(cells[0].text.strip())

                last_number = number

                td_code = next(iter(cells[2].contents), None)
                if not td_code:
                    logger.warning(
                        f"Empty code cell at {number}",
                    )
                    continue

                try:
                    code = int(str(td_code).strip())
                except ValueError:
                    continue

                priority = int(cells[-1].text.strip())

                try:
                    score = int(cells[4].text.strip())
                except ValueError:
                    score = 0

                is_preferred = False
                has_agreement = cells[-2] == "Да"

                student = Student(
                    number=number,
                    code=code,
                    priority=priority,
                    score=score,
                    is_preferred=is_preferred,
                    has_agreement=has_agreement,
                )
                students.append(student)

            speciality.students = students
            speciality.total_students = last_number
