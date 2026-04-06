import struct
import time
from typing import Dict

import smbus2

from errors import SensorSetupError, SensorTimeoutError
from logs import get_logger
from sensors.base import AbstractSensor, SensorCapability
from utils import get_instant

logger = get_logger("SENSOR", sub="YL69")

# ── Registradores do ADS1115 ───────────────────────────────────────────────
_REG_CONVERSION = 0x00
_REG_CONFIG     = 0x01

_OS_SINGLE   = 0x8000
_MODE_SINGLE = 0x0100

_MUX = {
    0: 0x4000,
    1: 0x5000,
    2: 0x6000,
    3: 0x7000,
}

# PGA ±4.096V — cobre bem a faixa 0-3.3V do YL-69
_PGA_4096 = 0x0200
_FSR_4096 = 4.096

_DR_128SPS            = 0x0080
_CONVERSION_TIMEOUT_S = 0.1

# Tensões de calibração — ajustar conforme medição real do sensor
_V_DRY_DEFAULT = 3.3   # V — solo seco (resistência máxima)
_V_WET_DEFAULT = 0.5   # V — solo saturado (resistência mínima)


class YL69SoilMoistureSensor(AbstractSensor):
    sensor_name = "Soil Moisture Sensor"
    model = "YL-69"
    capabilities = ["humidity"]
    interface = "I2C"

    def configure(self, **params) -> None:
        """
        Parâmetros esperados:
            - i2c_bus     (int)   : Barramento I2C (padrão: 1)
            - i2c_address (int)   : Endereço I2C do ADS1115 (padrão: 0x48)
            - adc_channel (int)   : Canal do ADS1115 (padrão: 1)
            - v_dry       (float) : Tensão em solo seco para calibração (padrão: 3.3V)
            - v_wet       (float) : Tensão em solo saturado para calibração (padrão: 0.5V)
        """
        self.i2c_bus     = int(params.get("i2c_bus", 1))
        self.i2c_address = params.get("i2c_address", 0x48)
        if isinstance(self.i2c_address, str):
            self.i2c_address = int(self.i2c_address, 0)
        self.adc_channel = int(params.get("adc_channel", 0))
        self.v_dry       = float(params.get("v_dry", _V_DRY_DEFAULT))
        self.v_wet       = float(params.get("v_wet", _V_WET_DEFAULT))

        if self.adc_channel not in _MUX:
            raise ValueError(f"adc_channel deve ser 0–3, recebido: {self.adc_channel}")

        logger.debug(
            "I2C: (bus=%s, address=0x%02X, channel=%s) | calibração: dry=%.2fV wet=%.2fV",
            self.i2c_bus,
            self.i2c_address,
            self.adc_channel,
            self.v_dry,
            self.v_wet,
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
        logger.debug("Executando probe do sensor")

        if not self.is_initialized:
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

    def read(self) -> Dict[str, float]:
        """
        Retorna a umidade do solo em porcentagem (0–100%).

        Fórmula:
            V_out     = raw × (FSR / 32767)
            moisture% = clamp((V_dry - V_out) / (V_dry - V_wet) × 100, 0, 100)

        Quanto mais úmido o solo → menor resistência → menor tensão de saída.
        """
        if not self.is_initialized:
            self.setup()

        raw       = self._read_ads1115()
        voltage_v = raw * (_FSR_4096 / 32767.0)

        moisture = (self.v_dry - voltage_v) / (self.v_dry - self.v_wet) * 100.0
        moisture = round(max(0.0, min(100.0, moisture)), 2)

        logger.debug(
            "raw=%s  tensão=%.4fV  umidade=%.2f%%",
            raw,
            voltage_v,
            moisture,
        )

        return {
            SensorCapability.HUMIDITY: moisture,
            "measuredAt": get_instant(),
        }

    # ------------------------------------------------------------------ #
    # I2C privado                                                          #
    # ------------------------------------------------------------------ #

    def _read_ads1115(self) -> int:
        config = (
            _OS_SINGLE
            | _MUX[self.adc_channel]
            | _PGA_4096
            | _MODE_SINGLE
            | _DR_128SPS
        )

        high_byte = (config >> 8) & 0xFF
        low_byte  =  config       & 0xFF
        self._bus.write_i2c_block_data(
            self.i2c_address, _REG_CONFIG, [high_byte, low_byte]
        )

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

        data = self._bus.read_i2c_block_data(self.i2c_address, _REG_CONVERSION, 2)
        return struct.unpack(">h", bytes(data))[0]

    # ------------------------------------------------------------------ #
    # Identidade                                                           #
    # ------------------------------------------------------------------ #

    @property
    def local_id(self) -> str:
        return (
            f"humidity:yl69"
            f":i2c{self.i2c_bus}"
            f":0x{self.i2c_address:02X}"
            f":{self.adc_channel}"
        )

    def shutdown(self) -> None:
        logger.info("Desligando sensor...")
        if hasattr(self, "_bus"):
            self._bus.close()
