from harvesting.edu.etu import Harvester as EtuHarvester
from harvesting.edu.spbstu import Harvester as EtuSpbStu

EDU_MAPPER = {
    "ЛЭТИ": EtuHarvester,
    "Политех": EtuSpbStu,
}
