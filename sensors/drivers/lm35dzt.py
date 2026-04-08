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
        if not self.is_initialized:
            logger.debug("Sensor não inicializado, executando setup()")
            self.setup()

        print("\n========== READ START ==========")
        print(self.__str__())

        print("\n--- TESTE MÉDIA (5 leituras) ---")
        values = []
        for i in range(5):
            v = self._read_ads1115()
            print(f"RAW[{i}]: {v}")
            values.append(v)
        avg = sum(values) / len(values)
        print(f"MÉDIA RAW: {avg}")

        print("\n--- LEITURA FINAL ---")
        raw = self._read_ads1115()
        print(f"RAW FINAL: {raw}")

        voltage_v = raw * (_FSR_2048 / 32767.0)
        print(f"VOLTAGE: {voltage_v}")

        temperature_c = (voltage_v * 1000.0) / _MV_PER_CELSIUS
        print(f"TEMP_CALCULADA: {temperature_c}")

        result = round(temperature_c, 2)
        print(f"TEMP_FINAL (round): {result}")

        print("========== READ END ==========\n")

        return {
            SensorCapability.TEMPERATURE: result,
            "measuredAt": get_instant(),
        }

    def _read_ads1115(self) -> int:
        print("\n[ADS1115] Iniciando leitura")

        config = (
            _OS_SINGLE
            | _MUX[self.adc_channel]
            | _PGA_2048
            | _MODE_SINGLE
            | _DR_128SPS
        )

        print(f"[ADS1115] CONFIG: 0x{config:04X}")

        high_byte = (config >> 8) & 0xFF
        low_byte  =  config       & 0xFF

        print(f"[ADS1115] WRITE BYTES: [{high_byte:#04x}, {low_byte:#04x}]")

        self._bus.write_i2c_block_data(
            self.i2c_address, _REG_CONFIG, [high_byte, low_byte]
        )

        deadline = time.time() + _CONVERSION_TIMEOUT_S

        while True:
            data = self._bus.read_i2c_block_data(self.i2c_address, _REG_CONFIG, 2)
            cfg = (data[0] << 8) | data[1]

            print(f"[ADS1115] POLL CONFIG: 0x{cfg:04X}")

            if data[0] & 0x80:
                print("[ADS1115] Conversão pronta")
                break

            if time.time() > deadline:
                print("[ADS1115] TIMEOUT!")
                raise SensorTimeoutError(
                    "Timeout aguardando conversão do ADS1115",
                    sensor_id=self.api_id,
                )

            time.sleep(0.001)

        data = self._bus.read_i2c_block_data(self.i2c_address, _REG_CONVERSION, 2)
        print(f"[ADS1115] RAW BYTES: {data}")

        raw = struct.unpack(">h", bytes(data))[0]
        print(f"[ADS1115] RAW CONVERTIDO: {raw}")

        return raw

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