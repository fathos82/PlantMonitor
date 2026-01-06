import random
from typing import List

from sensors.sensors import AbstractSensor



ID = 1
class SensorTest(AbstractSensor):

    @property
    def local_id(self) -> str:
        return "id_teste"

    def probe(self) -> bool:
        return True

    def setup(self):
        pass

    def health(self) -> bool:
        return True

    def read(self):
        rand_value = random.random()
        return [rand_value] # todo: talvez isso vire um MAP ex: {umidade:1.1}

    @property
    def capabilities(self):
        return ["TEMPERATURE"]