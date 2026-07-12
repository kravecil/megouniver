import asyncio
import logging
from typing import Self

from harvesting.fetcher import Fetcher
from harvesting.interfaces import IHarvestable
from harvesting.models import Speciality, Student

logger = logging.getLogger(__name__)


class Harvester(IHarvestable):
    name = "Политех"

    URL_CODE_LIST = "https://my.spbstu.ru/home/get-code-list"
    URL_DIRECTION_INFO = "https://my.spbstu.ru/home/get-direction-info"
    URL_ABIT_LIST = "https://my.spbstu.ru/home/get-abit-list"

    HEADERS_UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 YaBrowser/26.4.0.0 Safari/537.36"

    def __init__(self, fetcher: Fetcher | None) -> None:
        self.fetcher = fetcher

    @classmethod
    async def create(cls) -> Self:
        fetcher = Fetcher()

        return cls(fetcher=fetcher)

    async def harvest(self) -> list[Speciality]:
        if self.fetcher is None:
            raise ValueError("Fetcher is not initialized")

        logger.info("Harvesting SPBSTU...")

        sem = asyncio.Semaphore(10)

        async with self.fetcher:
            logger.info("Fetching code list...")
            code_list = await self._get_code_list()

            logger.info("Found %d codes.", len(code_list))

            tasks = []
            for code, name in code_list.items():
                tasks.append(self._get_speciality_data(code, name, sem))

            specialities = await asyncio.gather(*tasks)

        return [s for s in specialities if s is not None]

    async def _get_code_list(self) -> dict[int, str]:
        if self.fetcher is None:
            raise ValueError("Fetcher is not initialized")

        if self.fetcher.client is None:
            raise ValueError("Client is not initialized")

        headers = {"User-Agent": self.HEADERS_UA}

        data = {"id_1": "2", "id_2": "1", "education_level": "bachelor"}

        try:
            data = await self.fetcher.fetch(
                url=self.URL_CODE_LIST,
                method="post",
                headers=headers,
                data_type="json",
                data=data,
            )

            code_list = data.get("code_list")
            if not code_list:
                logger.error("Code list is none or empty")
                return {}

            result = {each["id"]: each["title"] for each in code_list}

            return result
        except Exception as e:
            logger.error("Failed to fetch code list: %s", str(e), exc_info=True)
            return {}

    async def _get_speciality_data(
        self, code: int, name: str, sem: asyncio.Semaphore
    ) -> Speciality | None:
        if self.fetcher is None:
            raise ValueError("Fetcher is not initialized")

        if self.fetcher.client is None:
            raise ValueError("Client is not initialized")

        try:
            async with sem:
                max_places, students = await asyncio.gather(
                    self._get_max_places(code), self._get_students(code)
                )

            return Speciality(
                name=name,
                max_places=max_places,
                students=students,
                total_students=len(students),
            )
        except Exception as e:
            logger.error(f"Error parsing specialty {name}: %s", e)
            return None

    async def _get_max_places(self, code) -> int:
        if self.fetcher is None:
            raise ValueError("Fetcher is not initialized")

        if self.fetcher.client is None:
            raise ValueError("Client is not initialized")

        headers = {"User-Agent": self.HEADERS_UA}

        get_info_task_data = {
            "id_3": code,
            "education_level": "bachelor",
            "condition": "1",
        }

        result = await self.fetcher.fetch(
            url=self.URL_DIRECTION_INFO,
            method="post",
            data_type="json",
            data=get_info_task_data,
            headers=headers,
        )

        return result[0].get("places", 0)

    async def _get_students(self, code: int) -> list[Student]:
        if self.fetcher is None:
            raise ValueError("Fetcher is not initialized")

        if self.fetcher.client is None:
            raise ValueError("Client is not initialized")

        headers = {"User-Agent": self.HEADERS_UA}

        params = {
            "filter_1": 2,
            "filter_2": 1,
            "filter_3": code,
            "education_level": "bachelor",
        }

        data = await self.fetcher.fetch(
            url=self.URL_ABIT_LIST, headers=headers, params=params, data_type="json"
        )

        students_list = data.get("results", [])

        students = []
        for student in students_list:
            number = student["num"]
            code_ = int(student["code"])
            priority = student["priority"]
            score = student["sum"]
            is_preferred = student["privilege"] != "Отсутствует"
            students.append(
                Student(
                    number=number,
                    code=code_,
                    priority=priority,
                    score=score,
                    is_preferred=is_preferred,
                )
            )

        return students
