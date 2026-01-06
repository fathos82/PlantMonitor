import json
from abc import ABC, abstractmethod
from typing import List, Optional, Dict


from enum import Enum


class SensorCapability(str, Enum):
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
    QUALITY = "quality"
    STATUS = "status"

    # Energia
    VOLTAGE = "voltage"
    CURRENT = "current"
    POWER = "power"
    BATTERY_LEVEL = "battery_level"


class AbstractSensor(ABC):

    """
    Contrato base para qualquer sensor físico ou lógico
    """

    # ===== Identidade do sistema =====
    api_id: Optional[int] = None          # ID retornado pela API
    capabilities:List[SensorCapability] = []
    is_initialized: bool = False
    # ===== Identidade física =====
    hardware_id: Optional[str] = None     # I2C addr, ROM ID, VID:PID

    # ===== Metadados =====
    sensor_name: Optional[str] = None
    model: Optional[str] = None
    interface = "GPIO"       # I2C, GPIO, USB, 1WIRE, SPI

    # ===== Ciclo de vida =====
    @abstractmethod
    def probe(self) -> bool:
        """Detecta se o sensor existe fisicamente"""
        raise NotImplementedError

    @abstractmethod
    def setup(self) -> None:
        """Configura o sensor após detecção"""
        raise NotImplementedError

    @abstractmethod
    def read(self) ->  Dict[str, float]:
        """Retorna leitura atual do sensor"""
        raise NotImplementedError

    def health(self) -> bool:
        """Verifica se o sensor está saudável"""
        return True


    # ===== Identificador físico determinístico =====
    @property
    @abstractmethod
    def local_id(self) -> str:
        """
        Ex:
          I2C:1:0x76
          GPIO:17:YL-69
          1WIRE:28-xxxx
        """
        raise NotImplementedError
    @property
    def capabilities_values(self):
        return [cap.name for cap in self.capabilities]
    # ===== Serialização =====
    def to_dict(self) -> dict:
        return {
            "apiId": self.api_id,
            "localId": self.local_id,
            "model": self.model,
            "interface": self.interface,
            "capabilities": self.capabilities_values,
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
