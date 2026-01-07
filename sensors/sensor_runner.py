import threading
import queue
import time
from enum import Enum, auto

from sensors.sensors import AbstractSensor
from settings import SENSOR_SLEEP_TIME
from utils import send_data


class Command(Enum):
    START = auto()
    STOP = auto()
    RELOAD = auto()
    SHUTDOWN = auto() 


class SensorRunner(threading.Thread):

    def __init__(self, sensor:AbstractSensor):
        super().__init__(daemon=True)
        self.sensor = sensor
        self.commands = queue.Queue()
        self.running = False
        self._stop_requested = False

    def run(self):
        print(f"[RUNNER] iniciado: {self.sensor.local_id}")

        while not self._stop_requested:
            self._handle_commands()

            if not self.running:
                time.sleep(0.1)
                continue

            try:
                value = self.sensor.read()
                send_data(value, self.sensor)
                print(f"[RUNNER] leitura: {value}")
            except Exception as e:
                # todo: informar API que não está integro
                # todo: a depender do erro tentar a reinicialização
                # todo: enviar mensagem de acordo com erro
                print(f"[RUNNER][ERRO] {e}")

            time.sleep(SENSOR_SLEEP_TIME)

        print(f"[RUNNER] finalizado: {self.sensor.local_id}")

    def _handle_commands(self):
        try:
            command = self.commands.get_nowait()
        except queue.Empty:
            return

        print(f"[RUNNER] comando recebido: {command.name}")

        match command:
            case Command.START:
                self.running = True

            case Command.STOP:
                self.sensor.shutdown()
                self.running = False
                self._stop_requested = True
                self.sensor.shutdown()

            case Command.RELOAD:
                self._reload_sensor()

            case _:
                print(f"[RUNNER][WARN] comando desconhecido: {command}")

    def _reload_sensor(self):
        print(f"[RUNNER] recarregando sensor {self.sensor.local_id}")
        try:
            self.sensor.is_initialized = False
            self.sensor.setup()
        except Exception as e:
            print(f"[RUNNER][ERRO][RELOAD] {e}")

