import threading
import time

import utils
from api import mqtt
from errors import SensorError
from logs import get_logger
from sensors.base import AbstractSensor
from settings import SENSOR_SLEEP_TIME, SENSOR_ERROR_SLEEP_TIME
from api.client import send_sensor_error


class SensorRunner(threading.Thread):

    def __init__(self, sensor: AbstractSensor):
        super().__init__(daemon=True)

        self.sensor = sensor
        self._stop_requested = False
        self.had_error = False
        self._lock = threading.Lock()
        self.logger = get_logger(
            "SENSOR_WORKER",
            sub=sensor.model,
            sensor_id=getattr(sensor, "api_id", None)
        )

        self.logger.debug("Worker criado")

    def stop(self):
        self.logger.info("Encerrando sensor")
        with self._lock:
            self._stop_requested = True
            self.sensor.shutdown()

    def reload(self):
        self.logger.warning("Recarregando sensor")
        with self._lock:
            self._reload_sensor()

    def update(self, **kwargs):
        self.logger.info("Atualizando parâmetros do sensor")
        with self._lock:
            self.sensor.configure(**kwargs)
            self.sensor.setup()

    def run(self):
        self.logger.info("Worker iniciado")

        self.initialize_sensor()

        while not self._stop_requested:
            with self._lock:
                if self._stop_requested:
                    break

                if self.had_error:
                    self._handle_error()
                    continue

                try:
                    value = self.sensor.read()
                    value["measuredAt"] = utils.get_instant()
                    mqtt.send_data(value, self.sensor)
                    self.logger.debug("Leitura realizada com sucesso", extra={"value": value})

                except SensorError as e:
                    self.had_error = True
                    self.logger.error("Erro na leitura do sensor", extra={"error": str(e)})
                    send_sensor_error(message=str(e), sensor_id=self.sensor.api_id)

                except Exception:
                    self.had_error = True
                    self.logger.exception("Erro inesperado durante leitura do sensor")
                    send_sensor_error(
                        message="Erro inesperado ao tentar realizar leitura no sensor.",
                        sensor_id=self.sensor.api_id,
                    )

            time.sleep(SENSOR_SLEEP_TIME)  # fora do lock

        self.logger.info("Worker finalizado")  # fora do while


    def initialize_sensor(self):
        if not self.sensor.probe():
            self.logger.error("Sensor {self.sensor.model} não respondeu a verificação da configuração dos pinos.")
            send_sensor_error(
                message=(
                    f"Sensor {self.sensor.model} não respondeu a verificação da configuração dos pinos. "
                    "Verifique a conexão física, configuração dos pinos e disponibilidade do hardware. "
                    "O sistema continuará tentando realizar leituras com o sensor mesmo falhando."
                ),
                sensor_id=self.sensor.api_id,
            )


    def _reload_sensor(self):
        try:
            self.sensor.setup()
            self.logger.info("Sensor reinicializado com sucesso")

        except Exception:
            self.logger.exception("Falha ao reinicializar o sensor")

    def _handle_error(self):
        self.logger.warning("Tratando erro do sensor")
        self.had_error = False  # erro sendo tratado aqui

        if self.sensor.probe():
            self.logger.info("Sensor respondeu ao probe — continuando")
            return

        self.logger.warning("Sensor não respondeu ao probe — tentando reload")
        self._reload_sensor()
        time.sleep(SENSOR_ERROR_SLEEP_TIME)
