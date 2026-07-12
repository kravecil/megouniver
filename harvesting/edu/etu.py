import asyncio
import logging
import re
from typing import Self

from bs4 import BeautifulSoup
from yarl import URL

from harvesting.fetcher import Fetcher
from harvesting.interfaces import IHarvestable
from harvesting.models import Speciality, Student
from harvesting.utils import get_page_id_from_url

logger = logging.getLogger(__name__)


class Harvester(IHarvestable):
    name = "ЛЭТИ"

    BASE_URL: str = "https://abit.etu.ru/ru/postupayushhim/lists/page/#/?id=019ee529-454f-7e45-aced-7f2361797e11"

    def __init__(self, page_id: str, fetcher: Fetcher | None) -> None:
        self.fetcher = fetcher
        self.page_id = page_id

    @classmethod
    async def create(cls) -> Self:
        fetcher = Fetcher()

        page_id = get_page_id_from_url(cls.BASE_URL)
        if not page_id:
            raise ValueError(f"Invalid URL: {cls.BASE_URL}")

        return cls(fetcher=fetcher, page_id=page_id)

    async def harvest(self) -> list[Speciality]:
        if self.fetcher is None:
            raise ValueError("Fetcher is not initialized")

        async with self.fetcher:
            specialities_data = await self._get_specialities_data()

            sem = asyncio.Semaphore(5)

            tasks = [
                self._gather_students_data(
                    page_id=page_id, speciality=speciality, sem=sem
                )
                for page_id, speciality in specialities_data.items()
            ]

            await asyncio.gather(*tasks)

        filtered_specialities = [
            s for s in specialities_data.values() if s.students is not None
        ]

        return filtered_specialities

    async def _get_specialities_data(self) -> dict[str, Speciality]:
        if self.fetcher is None:
            raise ValueError("Fetcher is not initialized")

        if self.fetcher.client is None:
            raise ValueError("Client is not initialized")

        logger.info("Fetching specialities data")
        try:
            html = await self.fetcher.fetch(
                self._get_specialities_body_url(self.page_id)
            )

            soup = BeautifulSoup(html, "lxml")

            list_div = soup.find("div", id="list")
            if not list_div:
                logger.warning("No #list div found")
                return {}

            table = list_div.find("table", class_="table")
            if not table:
                logger.warning("No .table found inside #list")
                return {}

            rows = table.find_all("tr")
            rows_to_process = rows[2:]

            result = {}
            for row in rows_to_process:
                parsed = self._parse_specialities_table_row_cells(row)
                if not parsed:
                    continue

                page_id, speciality = parsed
                if speciality:
                    result[page_id] = speciality

            logger.info(f"Fetched {len(result)} specialities data")

            return result

        except Exception as e:
            logger.error("Failed to fetch specialties data: %s", e)
            return {}

    @staticmethod
    def _parse_specialities_table_row_cells(row) -> tuple[str, Speciality] | None:
        cells = row.find_all("td")

        if cells:
            code = cells[0].text.strip()
            name = cells[1].text.strip()

            a_tag = cells[2].find("a")
            if a_tag is None:
                logger.info("No <a> tag found in cell: %s", cells[2])
                return None
            if a_tag["href"] is None:
                logger.info("No href attribute found in <a> tag: %s", a_tag)
                return None

            page_id = get_page_id_from_url(str(a_tag["href"]))
            if page_id is None:
                logger.info("No page_id found in href attribute: %s", a_tag["href"])
                return None

            speciality = Speciality(name=f"{code} {name}")

            return page_id, speciality

    async def _gather_students_data(
        self, page_id: str, speciality: Speciality, sem: asyncio.Semaphore
    ) -> list[Student] | None:
        if self.fetcher is None:
            raise ValueError("Fetcher is not initialized")

        if self.fetcher.client is None:
            raise ValueError("Client is not initialized")

        logger.info(f"Fetching students data for {speciality.name})")

        async with sem:
            try:
                url = self._get_students_body_url(page_id)
                html = await self.fetcher.fetch(url)
                soup = BeautifulSoup(html, "lxml")

                max_places = self._get_max_places(soup)
                if max_places is None:
                    return None

                speciality.max_places = max_places
                logger.info(
                    f"Max places for {speciality.name}: {speciality.max_places}"
                )

                tbody = soup.find("tbody", id="lists-tbody")
                if not tbody:
                    logger.warning("No .table found")
                    return None

                rows = tbody.find_all("tr")
                result = []
                for row in rows:
                    student = self._parse_students_table_row_cells(row)
                    if student:
                        result.append(student)

                if result:
                    speciality.students = result
                    speciality.total_students = len(result)
                    logger.info(f"Fetched {len(result)} students data")
                else:
                    logger.warning(f"No students data found for {speciality.name})")
            except Exception as e:
                logger.error(
                    f"Failed to fetch students data for {speciality.name}: {e}"
                )
                return None

    @staticmethod
    def _get_max_places(soup: BeautifulSoup) -> int | None:
        places_div = soup.find("div", class_="places-list")
        if not places_div:
            logger.warning("No .places-list found")
            return None

        text = places_div.text.strip()

        match = re.search(r"\d+", text)
        if match:
            return int(match.group())

        return None

    @staticmethod
    def _parse_students_table_row_cells(row) -> Student | None:
        cells = row.find_all("td")

        if not cells:
            return None

        number = int(cells[0].text.strip())
        code = int(cells[1].text.strip())
        priority = int(cells[2].text.strip())
        score = int(cells[4].text.strip())
        is_preferred = cells[11].text.strip().lower() == "да"

        return Student(
            number=number,
            code=code,
            priority=priority,
            score=score,
            is_preferred=is_preferred,
        )

    @staticmethod
    def _get_specialities_body_url(page_id: str) -> str:
        base_url = "https://lists.priem.etu.ru/public/page.html"

        url = URL(base_url).with_query(id=page_id)

        return str(url)

    @staticmethod
    def _get_students_body_url(page_id: str, is_body_only: bool = False) -> str:
        base_url = "https://lists.priem.etu.ru/public/list.html"

        url = URL(base_url).with_query(id=page_id, body_only=str(is_body_only))

        return str(url)
