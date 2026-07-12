from typing import Protocol, Self

from harvesting.models import Speciality


class IHarvestable(Protocol):
    name: str

    @classmethod
    async def create(cls) -> Self: ...

    async def harvest(self) -> list[Speciality]: ...
