import json
from abc import ABC, abstractmethod
from typing import List, Optional, Dict


from enum import Enum



class SensorCapability(str, Enum):
    MOCK = "mock"
    # Distância / Proximidade
    DISTANCE = "distance"
    PROXIMITY = "proximity"
    # Ambiente
    TEMPERATURE = "temperature"
    HUMIDITY = "humidity"
    PRESSURE = "pressure"
    LIGHT = "light"
    # Movimento / Posição
    ACCELERATION = "acceleration"
    GYROSCOPE = "gyroscope"
    ORIENTATION = "orientation"
    # Qualidade / Status
    SIGNAL_STRENGTH = "signal_strength"
    AIR_QUALITY = "air_quality"
    STATUS = "status"
    # Energia
    VOLTAGE = "voltage"
    CURRENT = "current"
    POWER = "power"
    BATTERY_LEVEL = "battery_level"

from enum import Enum

from enum import Enum
from typing import Type, TypeVar



E = TypeVar("E", bound=Enum)
from enum import Enum

class SensorModel(str, Enum):
    MQ135 = "MQ-135"
    MOCK = "MOCK"
    HC_SR04 = "HC-SR04"
    LM35DZ = "LM35DZ"
    BME280 = "BME280"
    DHT11 = "DHT11"
    DHT22 = "DHT22"
    YL_69 = "YL-69"
    BH1750 = "BH1750"
    MPU6050 = "MPU6050"
    GENERIC_GPIO = "GENERIC_GPIO"

    @classmethod
    def _missing_(cls, value):
        if isinstance(value, str):
            normalized = value.strip().upper().replace("-", "_")

            for member in cls:
                if member.value.replace("-", "_") == normalized:
                    return member

        # 👇 erro descritivo
        valid_values = [m.value for m in cls]
        raise ValueError(
            f"SensorModel inválido: '{value}'. "
            f"Valores válidos: {valid_values}"
        )
    @classmethod
    def _missing_(cls: Type[E], value: object) -> E:
        if value is None:
            raise ValueError("None is not a valid SensorModel")

        normalized = str(value).strip().upper().replace("-", "_")

        for member in cls:
            if member.name == normalized:
                return member

        raise ValueError(f"{value!r} is not a valid {cls.__name__}")




class AbstractSensor(ABC):
    """
    Contrato base para qualquer sensor físico ou lógico
    """

    def __init__(self, **kwargs):
        self.configure(**kwargs)
        self.setup()


    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if hasattr(cls, 'model') and cls.model is not None:
            from sensors.creator import sensor_creator
            sensor_creator.register(cls.model, cls)


    # ===== Identidade do sistema =====
    api_id: Optional[int] = None          # ID retornado pela API
    capabilities:List[SensorCapability] = []
    # ===== Identidade física =====
    hardware_id: Optional[str] = None     # I2C addr, ROM ID, VID:PID

    # ===== Metadados =====
    sensor_name: Optional[str] = None
    model: Optional[SensorModel] = None
    interface = "GPIO"       # I2C, GPIO, USB, 1WIRE, SPI

    # ===== Ciclo de vida =====
    @abstractmethod
    def configure(self, **params) -> None:
        pass
    @abstractmethod
    def probe(self) -> bool:
        """Detecta se o sensor existe fisicamente"""
        raise NotImplementedError

    @abstractmethod
    def setup(self) -> None:
        """Configura o sensor após detecção"""
        raise NotImplementedError

    @abstractmethod
    def read(self) ->  Dict[SensorCapability, float]:
        """Retorna leitura atual do sensor"""
        raise NotImplementedError

    def health(self) -> bool:
        """Verifica se o sensor está saudável"""
        return True

    @abstractmethod
    def shutdown(self) -> None:
        raise NotImplementedError

    # ===== Identificador físico determinístico =====


    # ===== Serialização =====
    def to_dict(self) -> dict:
        return {
            "apiId": self.api_id,
            # "localId": self.local_id,
            "model": self.model,
            "interface": self.interface,
            "capabilities": self.capabilities,
            "healthy": self.health(),
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False)

#
# class BME280Driver(SensorDriver):
#     ADDRESSES = [0x76, 0x77]
#
#     def __init__(self, bus):
#         self.bus = bus
#         self.address = None
#
#     def probe(self):
#         for addr in self.ADDRESSES:
#             try:
#                 chip_id = self.bus.read_byte_data(addr, 0xD0)
#                 if chip_id == 0x60:  # ID do BME280
#                     self.address = addr
#                     return True
#             except OSError:
#                 pass
#         return False
#
#     def setup(self):
#         # escreve registradores de configuração
#         pass
#
#     def read(self):
#         return {
#             "temperature": 24.7,
#             "humidity": 58.2,
#             "pressure": 1012.5
#         }
