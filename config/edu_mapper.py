from harvesting.edu.etu import Harvester as EtuHarvester
from harvesting.edu.guap import Harvester as GuapHarvester
from harvesting.edu.spbstu import Harvester as SpbStuHarvester

EDU_MAPPER = {
    "ЛЭТИ": EtuHarvester,
    "Политех": SpbStuHarvester,
    "ГУАП": GuapHarvester,
}
