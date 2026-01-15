import threading
import queue
import time
from enum import Enum, auto

import mqtt_client
from errors import SensorError
from logs import get_logger
from sensors.sensors import AbstractSensor
from settings import SENSOR_SLEEP_TIME, SENSOR_ERROR_SLEEP_TIME
from utils import send_to_api_error


class Command(Enum):
    START = auto()
    STOP = auto()
    RELOAD = auto()
    SHUTDOWN = auto()


class SensorRunner(threading.Thread):

    def __init__(self, sensor: AbstractSensor):
        super().__init__(daemon=True)

        self.sensor = sensor
        self.commands = queue.Queue()
        self.running = False
        self._stop_requested = False
        self.had_error = False

        # Logger contextualizado por sensor
        self.logger = get_logger(
            "SENSOR_WORKER",
            sub=sensor.model,
            sensor_id=getattr(sensor, "api_id", None)
        )

        self.logger.debug("Worker criado")

    def run(self):
        self.logger.debug("Worker iniciado")

        while not self._stop_requested:
            self._handle_commands()

            if not self.running:
                time.sleep(SENSOR_SLEEP_TIME)
                continue

            if self.had_error:
                self.handle_error()
                self.had_error = False

            try:
                value = self.sensor.read()
                mqtt_client.send_data(value, self.sensor)
                #
                # self.logger.debug(
                #     "Leitura realizada com sucesso",
                #     extra={"value": value}
                # )

            except SensorError as e:
                self.had_error = True
                self.logger.error(
                    "Erro na leitura do sensor",
                    extra={"error": str(e)}
                )
                send_to_api_error(
                   str(e),
                    sensor_id=self.sensor.api_id
                )


            except Exception:
                self.had_error = True
                self.logger.exception(
                    "Erro inesperado durante leitura do sensor"
                )
                send_to_api_error(
                    "Erro inesperado ao tentar realizar leitura no sensor.",
                    sensor_id=self.sensor.api_id
                )


            time.sleep(SENSOR_SLEEP_TIME)

        self.logger.debug("Worker finalizado")

    def _handle_commands(self):
        try:
            command = self.commands.get_nowait()
        except queue.Empty:
            return

        self.logger.debug("Comando recebido",extra={"command": command.name})

        match command:
            case Command.START:
                self.running = True
                self.logger.info("Sensor iniciado")

            case Command.STOP | Command.SHUTDOWN:
                self.logger.info("Encerrando sensor")
                self.running = False
                self._stop_requested = True
                self.sensor.shutdown()

            case Command.RELOAD:
                self.logger.warning("Recarregando sensor")
                self._reload_sensor()

            case _:
                self.logger.warning("Comando desconhecido",extra={"command": command})

    def _reload_sensor(self):
        try:
            self.sensor.is_initialized = False
            self.sensor.setup()
            self.logger.info("Sensor reinicializado com sucesso")

        except Exception:
            self.logger.exception("Falha ao reinicializar o sensor")

    def handle_error(self):
        self.logger.warning("Tratando erro do sensor")

        if not self.sensor.probe():
            self.logger.warning("Sensor não respondeu ao probe, tentando reload")
            self._reload_sensor()
            time.sleep(SENSOR_ERROR_SLEEP_TIME)
