import asyncio
import logging
import sys

from analysing.analyser import Analyser
from config.settings import STUDENT_CODE
from harvesting.edu.etu import Harvester as EtuHarvester
from harvesting.edu.guap import Harvester as GuapHarvester
from harvesting.edu.kpfu import Harvester as KpfuHarvester
from harvesting.edu.spbstu import Harvester as SpbStuHarvester
from harvesting.edu.uust import Harvester as UustHarvester
from harvesting.interfaces import IHarvestable
from harvesting.utils import get_stats_text, specialities_to_flat_df

logging.basicConfig(
    level=logging.WARNING,
    stream=sys.stdout,
)

EDU_LIST: list[type[IHarvestable]] = [
    EtuHarvester,
    GuapHarvester,
    SpbStuHarvester,
    KpfuHarvester,
    UustHarvester,
]


logger = logging.getLogger(__name__)

GREEN_CHECK = "\033[92m✅\033[0m"
RED_CROSS = "\033[91m❌\033[0m"

GREEN_INFO = "\033[92m💡\033[0m"


async def harvest_and_analyse_data(cls_harvester: type[IHarvestable]) -> str:
    harvester = await cls_harvester.create()
    data = await harvester.harvest()

    specialities_df = specialities_to_flat_df(data)

    result = Analyser(specialities_df, STUDENT_CODE).analyse()

    if not result:
        result = f"{RED_CROSS} никуда"
    else:
        result = f"{GREEN_CHECK} {result}"

    stats = get_stats_text(specialities_df, STUDENT_CODE)

    return f"{GREEN_INFO} {harvester.name}\n\n{stats}\n\nКуда проходит: {result}"


async def main():
    # tasks = []

    # for e in EDU_LIST:
    #     tasks.append(harvest_and_analyse_data(e))

    # results: list[str] = await asyncio.gather(*tasks)

    results = []
    for e in EDU_LIST:
        result = await harvest_and_analyse_data(e)
        results.append(result)

    print("\n\n-----------------------------------\n\n".join(results))


asyncio.run(main())
