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


async def harvest_and_analyse_data(
    cls_harvester: type[IHarvestable],
) -> str:
    harvester = await cls_harvester.create()
    data = await harvester.harvest()

    specialities_df = specialities_to_flat_df(data)

    result = Analyser(specialities_df, STUDENT_CODE).analyse()

    if not result:
        result = "никуда"

    stats = get_stats_text(specialities_df, STUDENT_CODE)

    return f"{stats}\n\nКуда проходит: {result}"


async def main():
    tasks = []

    for k, v in EDU_MAPPER.items():
        tasks.append(harvest_and_analyse_data(v))

    results: list[str] = await asyncio.gather(*tasks)

    print("\n\n-----------------------------------\n\n".join(results))


if __name__ == "__main__":
    asyncio.run(main())
