import random
from typing import Dict

from sensors.base import AbstractSensor, SensorModel, SensorCapability


class MockSensor(AbstractSensor):
    """
    Sensor falso para desenvolvimento e testes locais.
    Não requer hardware — retorna valores aleatórios.
    """
    sensor_name = "Mock Sensor"
    model = SensorModel.MOCK
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

    def read(self) -> Dict[SensorCapability, float]:
        return {SensorCapability.MOCK: random.uniform(34.3, 35.0)}

    @property
    def capabilities(self):
        return [SensorCapability.MOCK]

    def shutdown(self) -> None:
        pass