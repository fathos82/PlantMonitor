import time
from datetime import datetime, timezone
from typing import Dict

import RPi.GPIO as GPIO

from errors import SensorSetupError, SensorTimeoutError
from logs import get_logger
from sensors.sensors import AbstractSensor, SensorCapability
from utils import get_instant

logger = get_logger("SENSOR", sub="HC_SR04")


class HCSR04DistanceSensor(AbstractSensor):
    sensor_name = "Ultrasonic Distance Sensor"
    model = "HC-SR04"
    capabilities = ["distance"]

    def __init__(self, **kwargs):
        self.is_initialized = False
        self.set_params(**kwargs)
        logger.info("Inicializando sensor {}...".format(self.sensor_name))
        logger.debug(
            "Pinos: (trigger_pin=%s, echo_pin=%s)",
            self.trigger_pin,
            self.echo_pin
        )

    def set_params(self, **kwargs) -> None:
        self.trigger_pin = int(kwargs.get("trigger_pin", 23))
        self.echo_pin = int(kwargs.get("echo_pin", 24))

    def setup(self) -> None:
        logger.info("Iniciando setup do sensor")

        try:
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(self.trigger_pin, GPIO.OUT)
            GPIO.setup(self.echo_pin, GPIO.IN)

            GPIO.output(self.trigger_pin, GPIO.LOW)
            time.sleep(0.05)

            self.is_initialized = True
            logger.info("Sensor inicializado com sucesso")

        except PermissionError as exc:
            logger.error("Permissão insuficiente para acessar GPIO")
            raise SensorSetupError(
                "Sensor indisponível por falta de permissão.",
                sensor_id=self.api_id
            ) from exc

        except Exception as exc:
            logger.exception("Erro ao configurar GPIO do sensor")
            raise SensorSetupError(
                "Falha ao configurar pinos GPIO do sensor.",
                sensor_id=self.api_id
            ) from exc

    def probe(self) -> bool:
        """
        Verifica se o sensor responde com um pulso de ECHO.
        """
        logger.debug("Executando probe do sensor")

        if not self.is_initialized:
            logger.debug("Sensor não inicializado, executando setup()")
            self.setup()

        GPIO.output(self.trigger_pin, GPIO.HIGH)
        time.sleep(0.00001)
        GPIO.output(self.trigger_pin, GPIO.LOW)

        timeout = time.time() + 0.05

        while GPIO.input(self.echo_pin) == 0:
            if time.time() > timeout:
                logger.warning("Timeout no probe (sem ECHO)")
                return False

        logger.debug("Probe bem-sucedido")
        return True

    def read(self) -> Dict[str, float]:
        """
        Retorna a distância em centímetros.
        """
        if not self.is_initialized:
            logger.debug("Sensor não inicializado, executando setup()")
            self.setup()

        GPIO.output(self.trigger_pin, GPIO.HIGH)
        time.sleep(0.00001)
        GPIO.output(self.trigger_pin, GPIO.LOW)

        timeout_start = time.time() + 0.05
        timeout_end = time.time() + 0.05

        while GPIO.input(self.echo_pin) == 0:
            if time.time() > timeout_start:
                logger.error("Timeout aguardando início do ECHO")
                raise SensorTimeoutError(
                    "Timeout aguardando início do ECHO",
                    sensor_id=self.api_id
                )

        start = time.time()

        while GPIO.input(self.echo_pin) == 1:
            if time.time() > timeout_end:
                logger.error("Timeout aguardando fim do ECHO")
                raise SensorTimeoutError(
                    "Timeout aguardando fim do ECHO",
                    sensor_id=self.api_id
                )

        end = time.time()

        duration = end - start
        distance_cm = (duration * 34300) / 2

        logger.debug("Distância medida: %.2f cm", distance_cm)

        return {
            SensorCapability.DISTANCE: distance_cm,
            "measuredAt": get_instant()
        }
    @property
    def local_id(self) -> str:
        local_id = f"distance:{self.trigger_pin}:{self.echo_pin}"
        logger.debug("local_id gerado: %s", local_id)
        return local_id

    def shutdown(self) -> None:
        logger.info("Desligando sensor...")
        # todo: shutdown
        GPIO.cleanup()
