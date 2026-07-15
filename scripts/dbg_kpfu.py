import asyncio

# from analysing.analyser import Analyser
# from config.settings import STUDENT_CODE
from harvesting.edu.kpfu import Harvester
from harvesting.utils import specialities_to_flat_df


async def main():
    harvester = await Harvester.create()

    data = await harvester.harvest()

    data_df = specialities_to_flat_df(data)

    # result = Analyser(data_df, STUDENT_CODE).analyse()

    pass


asyncio.run(main())
