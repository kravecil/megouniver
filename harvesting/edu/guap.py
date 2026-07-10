import asyncio
import logging
import re
from typing import Self

from bs4 import BeautifulSoup, Tag

from harvesting.fetcher import Fetcher
from harvesting.interfaces import IHarvestable
from harvesting.models import Speciality, Student

logger = logging.getLogger(__name__)


class Harvester(IHarvestable):
    BASE_URL = "https://priem.guap.ru"
    SPECIALITIES_URL = "https://priem.guap.ru/bach/lists/list_1_1_1_1"

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
            specialities = await self._get_specialities_data()

            gathering_tasks = []
            for s in specialities:
                gathering_tasks.append(self._gather_speciality_data(s, sem))

            await asyncio.gather(*gathering_tasks)

        return specialities

    async def _get_specialities_data(self) -> list[Speciality]:
        try:
            html = await self.fetcher.fetch(self.SPECIALITIES_URL)

            soup = BeautifulSoup(html, "lxml")

            table = soup.find("table", class_="table")
            if not table:
                logger.error("Table with specialties was NOT found")
                return []

            tbody = table.find("tbody")
            if not tbody:
                logger.warning("Body of the Table is missing")
                return []

            specialities = []
            for row in tbody.find_all("tr"):
                cells = row.find_all("td")

                if len(cells) < 3:
                    logger.warning("Row with less than three columns: %s", row)
                    continue

                code = cells[0].text.strip()
                name = cells[1].text.strip()

                try:
                    total_students = int(cells[2].text.strip())
                except ValueError, TypeError:
                    total_students = 0

                ref = None
                link = cells[2].find("a")
                if link:
                    ref = str(link.get("href")).replace("\\", "/")

                if ref is None:
                    continue

                specialities.append(
                    Speciality(
                        name=f"{code} {name}", total_students=total_students, ref=ref
                    )
                )

            return specialities
        except Exception as e:
            logger.error("Error fetching specialties: %s", e)
            return []

    async def _gather_speciality_data(
        self, speciality: Speciality, sem: asyncio.Semaphore
    ) -> None:
        async with sem:
            html = await self.fetcher.fetch(f"{self.BASE_URL}{speciality.ref}")

            soup = BeautifulSoup(html, "lxml")

            h3_tag = soup.find("h3", string=lambda t: t and "Количество" in t)  # type:ignore
            if not h3_tag:
                return

            h3_tag_text = h3_tag.get_text(strip=True)
            match = re.search(
                r"Количество мест за вычетом квот\s*-\s*(\d+)", h3_tag_text
            )
            if not match:
                return

            max_places = int(match.group(1))

            table = soup.find("table", class_="pk-ratings-table")
            if not table:
                return

            tbody = table.find("tbody")
            if not tbody:
                return

            speciality.max_places = max_places
            speciality.students = await self._get_students(tbody)

    async def _get_students(self, table_body: Tag) -> list[Student]:
        rows = table_body.find_all("tr")

        students = []
        for row in rows:
            cells = row.find_all("td")

            number = int(cells[0].text.strip())
            code = int(cells[1].text.strip())
            priority = int(cells[2].text.strip())

            try:
                score = int(cells[3].text.strip())
            except ValueError:
                score = 0

            students.append(
                Student(
                    number=number,
                    code=code,
                    priority=priority,
                    score=score,
                    is_preferred=False,
                )
            )
        return students
