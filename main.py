import asyncio
import logging
import sys

from analysing.analyser import Analyser
from config.edu_mapper import EDU_MAPPER
from config.settings import STUDENT_CODE
from harvesting.interfaces import IHarvestable
from harvesting.utils import specialities_to_flat_df

logging.basicConfig(
    level=logging.WARNING,
    stream=sys.stdout,
)


logger = logging.getLogger(__name__)


async def harvest_and_analyse_data(
    cls_harvester: type[IHarvestable],
) -> tuple[str, str] | None:
    harvester = await cls_harvester.create()
    data = await harvester.harvest()

    specialities_df = specialities_to_flat_df(data)

    result = Analyser(specialities_df, STUDENT_CODE).analyse()

    return result


async def main():
    tasks = []

    for k, v in EDU_MAPPER.items():
        tasks.append(harvest_and_analyse_data(v))

    results = await asyncio.gather(*tasks)

    print(results)


if __name__ == "__main__":
    asyncio.run(main())
