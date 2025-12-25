import random

from sensors.sensors import AbstractSensor


class SensorTest(AbstractSensor):
    def probe(self) -> bool:
        return True

    def setup(self):
        pass

    def health(self) -> bool:
        return True

    def read(self):
        rand_value = random.random()
        return [rand_value] # todo: talvez isso vire um MAP ex: {umidade:1.1}

    def capabilities(self):
        return ["air-quality"]
