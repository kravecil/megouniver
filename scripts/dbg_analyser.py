import asyncio

import pandas as pd

from analysing.analyser import Analyser
from harvesting.utils import get_stats_text

FILENAME = "specialities.csv"

STUDENT_CODE = 1190524


async def main():
    df = pd.read_csv(FILENAME)

    print(get_stats_text(df, STUDENT_CODE))

    analyser = Analyser(df, STUDENT_CODE)

    result = analyser.analyse()

    print(result)


asyncio.run(main())
