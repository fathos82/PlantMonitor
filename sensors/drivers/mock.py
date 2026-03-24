import random
from typing import Dict

from sensors.base import AbstractSensor


class MockSensor(AbstractSensor):
    """
    Sensor falso para desenvolvimento e testes locais.
    Não requer hardware — retorna valores aleatórios.
    """
    sensor_name = "Mock Sensor"
    model = "MOCK"
    api_id = 1

    @property
    def local_id(self) -> str:
        return "mock:0"

    def configure(self, **params) -> None:
        pass

    def probe(self) -> bool:
        return True

    def setup(self) -> None:
        self.is_initialized = True

    def health(self) -> bool:
        return True

    def read(self) -> Dict[str, float]:
        return {"temperature": random.uniform(20.0, 35.0)}

    @property
    def capabilities(self):
        return ["temperature"]

    def shutdown(self) -> None:
        pass