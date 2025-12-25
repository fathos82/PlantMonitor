import random
from abc import ABC, abstractmethod


class AbstractSensor(ABC):
    @abstractmethod
    def probe(self) -> bool:
        """Detecta se o sensor existe"""
        raise NotImplementedError
    @abstractmethod
    def setup(self):
        """Configura o sensor"""
        pass
    @abstractmethod
    def read(self) -> dict:
        """Lê os dados"""
        raise NotImplementedError
    @abstractmethod
    def health(self) -> bool:
        """Verifica se está saudável"""
        return True


    @abstractmethod
    def capabilities(self):
        pass




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
