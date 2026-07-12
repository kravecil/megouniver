import asyncio

from harvesting.fetcher import Fetcher

URL = "https://abit.etu.ru/ru/postupayushhim/lists/page/#/?id=019ee529-454f-7e45-aced-7f2361797e11"
# URL = "https://abit.etu.ru/ru/postupayushhim/lists/page/list#/?id=019ee537-60b6-7ec5-9d90-6735fa9511a3"


async def main():
    fetcher = Fetcher()

    async with fetcher:
        http = await fetcher.fetch(URL)

    pass


asyncio.run(main())
