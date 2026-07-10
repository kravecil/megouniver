import asyncio
import logging
import sys

from analysing.analyser import Analyser
from config.edu_mapper import EDU_MAPPER
from config.settings import STUDENT_CODE
from harvesting.interfaces import IHarvestable
from harvesting.utils import get_stats_text, specialities_to_flat_df

logging.basicConfig(
    level=logging.WARNING,
    stream=sys.stdout,
)


logger = logging.getLogger(__name__)

GREEN_CHECK = "\033[92m✅\033[0m"
RED_CROSS = "\033[91m❌\033[0m"

GREEN_INFO = "\033[92m💡\033[0m"


async def harvest_and_analyse_data(
    university_name: str, cls_harvester: type[IHarvestable]
) -> str:
    harvester = await cls_harvester.create()
    data = await harvester.harvest()

    specialities_df = specialities_to_flat_df(data)

    result = Analyser(specialities_df, STUDENT_CODE).analyse()

    if not result:
        result = f"{RED_CROSS} никуда"
    else:
        result = f"{GREEN_CHECK} {result}"

    stats = get_stats_text(specialities_df, STUDENT_CODE)

    return f"{GREEN_INFO} {university_name}\n\n{stats}\n\nКуда проходит: {result}"


async def main():
    tasks = []

    for k, v in EDU_MAPPER.items():
        tasks.append(harvest_and_analyse_data(k, v))

    results: list[str] = await asyncio.gather(*tasks)

    print("\n\n-----------------------------------\n\n".join(results))


if __name__ == "__main__":
    asyncio.run(main())
