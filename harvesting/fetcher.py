import asyncio
import logging
import random
from typing import Any, Literal, Self

from aiohttp import ClientSession, ClientTimeout, TCPConnector
from aiohttp.client_exceptions import (
    ClientConnectorError,
    ClientResponseError,
    ConnectionTimeoutError,
)

logger = logging.getLogger(__name__)


class Fetcher:
    def __init__(
        self, timeout: float = 10.0, max_retries: int = 3, delay_sec: float = 1.0
    ) -> None:
        self.timeout = timeout
        self.max_retries = max_retries
        self.delay_sec = delay_sec

        self.connector = TCPConnector(limit_per_host=10)
        self.client: ClientSession | None = None

    async def __aenter__(self) -> Self:
        if self.client is None:
            self.client = ClientSession(
                timeout=ClientTimeout(total=self.timeout), connector=self.connector
            )

        return self

    async def __aexit__(self, *args) -> None:
        if self.client is not None:
            await self.client.close()
            self.client = None

    async def fetch(
        self,
        url: str,
        *,
        method: str = "get",
        data_type: Literal["text", "json"] = "text",
        headers: dict = {},
        params: dict = {},
        data: dict = {},
    ) -> Any:
        if self.client is None:
            raise RuntimeError("Client is not initialized")

        logger.info("Fetching %s", url)

        for attempt in range(1, self.max_retries + 1):
            try:
                async with getattr(self.client, method)(
                    url, headers=headers, params=params, json=data
                ) as response:
                    response.raise_for_status()
                    return await getattr(response, data_type)()
            except (
                ClientResponseError,
                ClientConnectorError,
                ConnectionTimeoutError,
            ) as e:
                logger.error(
                    "Failed attempt %d/%d: %s",
                    attempt,
                    self.max_retries,
                    e,
                )

            await self._wait(attempt)
        else:
            raise RuntimeError("Failed to fetch data")

    async def _wait(self, attempt: int) -> None:
        if attempt < self.max_retries:
            delay = 2 ** (attempt - 1) * self.delay_sec
            jitter = random.uniform(0, delay * 0.5)

            await asyncio.sleep(delay + jitter)

        return None
