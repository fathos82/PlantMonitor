import struct
import time
from typing import Dict

import smbus2

from errors import SensorSetupError, SensorTimeoutError
from logs import get_logger
from sensors.base import AbstractSensor, SensorCapability, SensorModel
from utils import get_instant

logger = get_logger("SENSOR", sub="LM35DZ")

# ── Registradores do ADS1115 ───────────────────────────────────────────────
_REG_CONVERSION = 0x00
_REG_CONFIG     = 0x01

# Bits do registrador de configuração (16-bit)
_OS_SINGLE   = 0x8000  # Inicia conversão single-shot
_MODE_SINGLE = 0x0100  # Modo single-shot

# Multiplexador: canal single-ended (AINx vs GND)
_MUX = {
    0: 0x4000,  # AIN0
    1: 0x5000,  # AIN1
    2: 0x6000,  # AIN2
    3: 0x7000,  # AIN3
}

# PGA ±6.144 V → FSR = 6.144 V → 1 LSB ≈ 187.5 µV
# Com 5V e LM35DZ saindo no máximo ~1V (100°C), ±6.144V cobre com folga
_PGA_2048 = 0x0400
_FSR_2048 = 2.048

# Data rate: 128 SPS (padrão — ~8 ms por conversão)
_DR_128SPS = 0x0080

# Timeout para aguardar fim da conversão single-shot
_CONVERSION_TIMEOUT_S = 0.1

# Sensibilidade do LM35DZ: 10 mV/°C
_MV_PER_CELSIUS = 10.0


class LM35DZTemperatureSensor(AbstractSensor):
    sensor_name = "Analog Temperature Sensor"
    model = SensorModel.LM35DZ
    capabilities = [SensorCapability.TEMPERATURE]
    interface = "I2C"

    def configure(self, **params) -> None:
            """
            Parâmetros esperados:
                - i2c_bus (int)    : Barramento I2C do Raspberry Pi (padrão: 1 → /dev/i2c-1)
                - i2c_address (int): Endereço I2C do ADS1115 (padrão: 0x48, pino ADDR → GND)
                - adc_channel (int): Canal do ADS1115 onde o LM35DZ está ligado (padrão: 0)

            Endereços disponíveis conforme pino ADDR do ADS1115:
                ADDR → GND : 0x48  (padrão)
                ADDR → VDD : 0x49
                ADDR → SDA : 0x4A
                ADDR → SCL : 0x4B
            """
            self.i2c_bus     = int(params.get("i2c_bus", 1))
            self.i2c_address  = params.get("i2c_address", 0x48)
            if isinstance(self.i2c_address, str):
                self.i2c_address = int(self.i2c_address, 0)

            self.adc_channel = int(params.get("adc_channel", 0))

            if self.adc_channel not in _MUX:
                raise ValueError(f"adc_channel deve ser 0–3, recebido: {self.adc_channel}")

            logger.debug(
                "I2C: (bus=%s, address=0x%02X, channel=%s)",
                self.i2c_bus,
                self.i2c_address,
                self.adc_channel,
            )

    def setup(self) -> None:
        logger.info("Iniciando setup do sensor")

        try:
            self._bus = smbus2.SMBus(self.i2c_bus)
            time.sleep(0.05)

            self.is_initialized = True
            logger.info("Sensor inicializado com sucesso")

        except PermissionError as exc:
            logger.error("Permissão insuficiente para acessar barramento I2C")
            raise SensorSetupError(
                "Sensor indisponível por falta de permissão.",
                sensor_id=self.api_id,
            ) from exc

        except Exception as exc:
            logger.exception("Erro ao abrir barramento I2C")
            raise SensorSetupError(
                "Falha ao configurar barramento I2C do sensor.",
                sensor_id=self.api_id,
            ) from exc

    def probe(self) -> bool:
        """
        Verifica se o ADS1115 responde no endereço I2C configurado
        tentando ler o registrador de configuração.
        """
        logger.debug("Executando probe do sensor")

        if not self.is_initialized:
            logger.debug("Sensor não inicializado, executando setup()")
            self.setup()

        try:
            self._bus.read_i2c_block_data(self.i2c_address, _REG_CONFIG, 2)
            logger.debug("Probe bem-sucedido")
            return True

        except OSError:
            logger.warning("Probe falhou — ADS1115 não encontrado em 0x%02X", self.i2c_address)
            return False

        except Exception:
            logger.exception("Erro inesperado durante probe")
            return False

    def read(self) -> Dict[SensorCapability, float]:
        """
        Dispara uma conversão single-shot no ADS1115, aguarda o resultado
        e retorna a temperatura em graus Celsius.

        Fórmula:
            V_out (V) = raw × (FSR / 32767)
            T (°C)    = (V_out × 1000) / 10
        """
        if not self.is_initialized:
            logger.debug("Sensor não inicializado, executando setup()")
            self.setup()
        print(self.__str__())
        print("TESTE: ")
        print(sum(self._read_ads1115() for _ in range(5)) / 5)
        raw = self._read_ads1115()
        print("RAW: {}".format(raw))

        # raw é signed 16-bit; valores negativos são ruído elétrico próximo
        # ao GND — clampamos em 0 pois o LM35DZ com 5V não vai abaixo de 0°C
        # if raw < 0:
        #     logger.debug("raw negativo (%s) clampado para 0", raw)
        #     raw = 0

        voltage_v     = raw * (_FSR_2048 / 32767.0)
        temperature_c = (voltage_v * 1000.0) / _MV_PER_CELSIUS

        logger.debug(
            "raw=%s  tensão=%.4fV  temperatura=%.2f°C",
            raw,
            voltage_v,
            temperature_c,
        )

        return {
            SensorCapability.TEMPERATURE: round(temperature_c, 2),
            "measuredAt": get_instant(),
        }

    # ------------------------------------------------------------------ #
    # I2C privado                                                          #
    # ------------------------------------------------------------------ #

    def _read_ads1115(self) -> int:
        """
        Configura e dispara uma conversão single-shot no ADS1115.
        Aguarda o bit OS indicar conversão concluída e retorna
        o valor bruto signed de 16 bits.
        """
        config = (
            _OS_SINGLE
            | _MUX[self.adc_channel]
            | _PGA_2048
            | _MODE_SINGLE
            | _DR_128SPS
        )

        high_byte = (config >> 8) & 0xFF
        low_byte  =  config       & 0xFF
        self._bus.write_i2c_block_data(
            self.i2c_address, _REG_CONFIG, [high_byte, low_byte]
        )

        # Polling do bit OS (bit 15): OS=1 indica conversão concluída
        deadline = time.time() + _CONVERSION_TIMEOUT_S
        while True:
            data = self._bus.read_i2c_block_data(self.i2c_address, _REG_CONFIG, 2)
            if data[0] & 0x80:
                break
            if time.time() > deadline:
                raise SensorTimeoutError(
                    "Timeout aguardando conversão do ADS1115",
                    sensor_id=self.api_id,
                )
            time.sleep(0.001)

        # Lê o registrador de conversão: 2 bytes big-endian signed
        data = self._bus.read_i2c_block_data(self.i2c_address, _REG_CONVERSION, 2)
        return struct.unpack(">h", bytes(data))[0]

    # ------------------------------------------------------------------ #
    # Identidade                                                           #
    # ------------------------------------------------------------------ #

    @property
    def local_id(self) -> str:
        local_id = (
            f"temperature:lm35dz"
            f":i2c{self.i2c_bus}"
            f":0x{self.i2c_address:02X}"
            f":{self.adc_channel}"
        )
        logger.debug("local_id gerado: %s", local_id)
        return local_id

    # ------------------------------------------------------------------ #
    # Ciclo de vida                                                        #
    # ------------------------------------------------------------------ #

    def shutdown(self) -> None:
        logger.info("Desligando sensor...")
        if hasattr(self, "_bus"):
            self._bus.close()

    def __str__(self) -> str:
        return (
            f"LM35DZTemperatureSensor(\n"
            f"  sensor_name={self.sensor_name},\n"
            f"  model={self.model},\n"
            f"  interface={self.interface},\n"
            f"  i2c_bus={getattr(self, 'i2c_bus', None)},\n"
            f"  i2c_address=0x{getattr(self, 'i2c_address', 0):02X},\n"
            f"  adc_channel={getattr(self, 'adc_channel', None)},\n"
            f"  is_initialized={getattr(self, 'is_initialized', False)},\n"
            f"  local_id={self.local_id if hasattr(self, 'i2c_bus') else None}\n"
            f")"
        )