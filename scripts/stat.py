"""
Скрипт для подсчёта расширенной статистики по университету по каждой специальности:
    - Общее количество заявлений
    - Количество свободных мест
    - Количество заявления, выше указанного общего балла (основных мест)
"""

import asyncio
import logging

from harvesting.edu.etu import Harvester as EtuHarvester
from harvesting.edu.guap import Harvester as GuapHarvester
from harvesting.edu.kpfu import Harvester as KpfuHarvester
from harvesting.edu.spbstu import Harvester as SpbstuHarvester
from harvesting.interfaces import IHarvestable

logging.disable(logging.CRITICAL)

SCORE_LIMIT = 263

EDU_LIST: list[type[IHarvestable]] = [
    # EtuHarvester,
    # GuapHarvester,
    # SpbstuHarvester,
    KpfuHarvester,
]


async def main():
    for edu_cls in EDU_LIST:
        # TODO @me: придумать что-нибудь получше, например, автоматическое определение
        score_limit = SCORE_LIMIT
        if edu_cls.name == "КФУ":
            score_limit -= 5

        harvester = await edu_cls.create()

        specialities = await harvester.harvest()

        print("-" * 40)
        print("📝 Статистика по ВУЗу [%s]\n" % harvester.name)

        for s in specialities:
            if s.max_places is None or s.students is None:
                continue

            print("📁 %s\t" % s.name)

            print("\t- Свободных мест: %d" % s.max_places)
            print("\t- Всего заявлений: %d" % s.total_students)

            places_up_to_score_limit = [
                a for a in s.students if a.score and a.score >= score_limit
            ]
            print(
                "\t- Количество основных мест >= %d: %d"
                % (score_limit, len(places_up_to_score_limit))
            )

    pass


asyncio.run(main())
