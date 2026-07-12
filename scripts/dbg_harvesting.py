import asyncio

from harvesting.edu.etu import Harvester
from harvesting.utils import specialities_to_flat_df

FILENAME = "specialities.csv"


async def main():
    harvester = await Harvester.create()
    result = await harvester.harvest()

    df_specialities = specialities_to_flat_df(result)
    df_specialities.to_csv(FILENAME)

    pass


asyncio.run(main())
