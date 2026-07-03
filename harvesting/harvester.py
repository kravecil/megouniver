import logging
from typing import Self

from bs4 import BeautifulSoup
from yarl import URL

from harvesting.fetcher import Fetcher
from harvesting.speciality import Speciality
from harvesting.utils import get_page_id_from_url

logger = logging.getLogger(__name__)


class Harvester:
    def __init__(self, page_id: str, fetcher: Fetcher | None) -> None:
        self.fetcher = fetcher
        self.page_id = page_id

    @classmethod
    async def create(cls, page_id: str) -> Self:
        fetcher = Fetcher()
        return cls(fetcher=fetcher, page_id=page_id)

    async def get_specialities_data(self) -> list[Speciality]:
        if self.fetcher is None:
            raise ValueError("Fetcher is not initialized")

        logger.info("Fetching specialities data")
        try:
            async with self.fetcher:
                html = await self.fetcher.fetch(
                    self._get_specialities_body_url(self.page_id)
                )

                soup = BeautifulSoup(html, "lxml")

                list_div = soup.find("div", id="list")
                if not list_div:
                    logger.warning("No #list div found")
                    return []

                table = list_div.find("table", class_="table")
                if not table:
                    logger.warning("No .table found inside #list")
                    return []

                rows = table.find_all("tr")
                rows_to_process = rows[2:]

                result = []
                for row in rows_to_process:
                    speciality = self._parse_table_row_cells(row)
                    if speciality:
                        result.append(speciality)

                logger.info(f"Fetched {len(result)} specialities data")

                return result

        except Exception as e:
            logger.error("Failed to fetch specialties data: %s", e)
            return []

    @staticmethod
    def _parse_table_row_cells(row) -> Speciality | None:
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

            speciality = Speciality(
                code=code,
                name=name,
                page_id=page_id,
            )

            return speciality

    @staticmethod
    def _get_specialities_body_url(page_id: str) -> str:
        BASE_URL = "https://lists.priem.etu.ru/public/page.html"

        url = URL(BASE_URL).with_query(id=page_id)

        return str(url)

    @staticmethod
    def _get_students_body_url(page_id: str, is_body_only: bool = True) -> str:
        BASE_URL = "https://lists.priem.etu.ru/public/list.html"

        url = URL(BASE_URL).with_query(id=page_id, body_only=is_body_only)

        return str(url)
