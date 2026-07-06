import asyncio
import logging
import sys

from analysing.analyser import Analyser
from harvesting.harvester import Harvester
from harvesting.utils import get_page_id_from_url, specialities_to_flat_df

logging.basicConfig(level=logging.INFO, stream=sys.stdout)

logger = logging.getLogger(__name__)


URL = "https://abit.etu.ru/ru/postupayushhim/lists/page/#/?id=019ee529-454f-7e45-aced-7f2361797e11"

STUDENT_CODE = 1190524


async def main():
    page_id = get_page_id_from_url(URL)

    if not page_id:
        raise ValueError(f"Invalid URL: {URL}")

    harvester = await Harvester.create(page_id)
    result = await harvester.harvest()

    df_specialities = specialities_to_flat_df(result)

    analyser = Analyser(df_specialities, STUDENT_CODE)

    result = analyser.analyse()

    print(result)


if __name__ == "__main__":
    asyncio.run(main())
