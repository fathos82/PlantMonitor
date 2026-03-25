from typing import Dict

import board
import busio
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn

from errors import SensorSetupError
from logs import get_logger
from sensors.base import AbstractSensor, SensorCapability
from utils import get_instant

logger = get_logger("SENSOR", sub="LM35DZ_ADAFRUIT")

_MUX = {
    0: ADS.P0,
    1: ADS.P1,
    2: ADS.P2,
    3: ADS.P3,
}

_MV_PER_CELSIUS = 10.0


class LM35DZTemperatureSensorAdafruit(AbstractSensor):
    """
    Wrapper da implementação LM35DZ usando a biblioteca
    Adafruit CircuitPython ADS1x15 via Blinka.

    Dependências:
        pip install adafruit-blinka adafruit-circuitpython-ads1x15

    Funcionalmente equivalente a LM35DZTemperatureSensor (smbus2),
    mas delega toda a comunicação I2C com o ADS1115 para a Adafruit.
    """

    sensor_name = "Analog Temperature Sensor (Adafruit)"
    model = "LM35DZ"
    capabilities = ["temperature"]
    interface = "I2C"

    def configure(self, **params) -> None:
        """
        Parâmetros esperados:
            - i2c_address (int): Endereço I2C do ADS1115 (padrão: 0x48, ADDR → GND)
            - adc_channel (int): Canal do ADS1115 onde o LM35DZ está ligado (padrão: 0)

        Endereços disponíveis conforme pino ADDR do ADS1115:
            ADDR → GND : 0x48  (padrão)
            ADDR → VDD : 0x49
            ADDR → SDA : 0x4A
            ADDR → SCL : 0x4B
        """
        self.i2c_address = int(params.get("i2c_address", 0x48))
        self.adc_channel = int(params.get("adc_channel", 0))

        if self.adc_channel not in _MUX:
            raise ValueError(f"adc_channel deve ser 0–3, recebido: {self.adc_channel}")

        logger.debug(
            "I2C: (address=0x%02X, channel=%s)",
            self.i2c_address,
            self.adc_channel,
        )

    def setup(self) -> None:
        logger.info("Iniciando setup do sensor")

        try:
            i2c = busio.I2C(board.SCL, board.SDA)
            self._ads = ADS.ADS1115(i2c, address=self.i2c_address)
            self._channel = AnalogIn(self._ads, _MUX[self.adc_channel])

            self.is_initialized = True
            logger.info("Sensor inicializado com sucesso")

        except PermissionError as exc:
            logger.error("Permissão insuficiente para acessar barramento I2C")
            raise SensorSetupError(
                "Sensor indisponível por falta de permissão.",
                sensor_id=self.api_id,
            ) from exc

        except Exception as exc:
            logger.exception("Erro ao inicializar ADS1115 via Adafruit")
            raise SensorSetupError(
                "Falha ao configurar o sensor via biblioteca Adafruit.",
                sensor_id=self.api_id,
            ) from exc

    def probe(self) -> bool:
        """
        Verifica se o ADS1115 responde tentando ler a tensão do canal.
        """
        logger.debug("Executando probe do sensor")

        if not self.is_initialized:
            logger.debug("Sensor não inicializado, executando setup()")
            self.setup()

        try:
            _ = self._channel.voltage
            logger.debug("Probe bem-sucedido")
            return True

        except Exception:
            logger.exception("Probe falhou")
            return False

    def read(self) -> Dict[str, float]:
        """
        Retorna a temperatura em graus Celsius.

        A Adafruit já entrega a tensão convertida em volts via
        channel.voltage — não é necessário lidar com raw ou FSR.

        Fórmula:
            T (°C) = (voltage × 1000) / 10
        """
        if not self.is_initialized:
            logger.debug("Sensor não inicializado, executando setup()")
            self.setup()

        voltage_v = self._channel.voltage

        # # Clamp para evitar temperaturas negativas por ruído elétrico
        # if voltage_v < 0:
        #     logger.debug("Tensão negativa (%.4fV) clampada para 0", voltage_v)
        #     voltage_v = 0.0

        temperature_c = (voltage_v * 1000.0) / _MV_PER_CELSIUS

        logger.debug(
            "tensão=%.4fV  temperatura=%.2f°C",
            voltage_v,
            temperature_c,
        )

        return {
            SensorCapability.TEMPERATURE: round(temperature_c, 2),
            "measuredAt": get_instant(),
        }

    @property
    def local_id(self) -> str:
        local_id = (
            f"temperature:lm35dz"
            f":0x{self.i2c_address:02X}"
            f":{self.adc_channel}"
        )
        logger.debug("local_id gerado: %s", local_id)
        return local_id

    def shutdown(self) -> None:
        logger.info("Desligando sensor...")
        if hasattr(self, "_ads"):
            self._ads.i2c_device.i2c.deinit()