from typing import Dict, Optional
# TODO: CRIAR BLACK_LIST
from api import client as api_client
from logs import get_logger
from sensors.base import SensorModel
from sensors.creator import sensor_creator
from sensors.runner import SensorRunner

logger = get_logger("SENSOR_POOL")


class SensorPool:
    def __init__(self):
        self._runners: Dict[int, SensorRunner] = {}
        self._publisher = None

    def set_publisher(self, publisher):
        self._publisher = publisher

    def discover(self, device_uuid: str):
        logger.info("Descoberta de sensores iniciada")

        sensors_data = api_client.get_sensors(device_uuid)

        if not sensors_data:
            logger.info("Nenhum sensor descoberto")
            return

        active_ids = set()

        for sensor_data in sensors_data:
            sensor_id = self._process_sensor_data(sensor_data)
            if sensor_id is not None:
                active_ids.add(sensor_id)

        self._remove_stale_runners(active_ids)

    def _process_sensor_data(self, sensor_data: dict):
        try:
            sensor_id = sensor_data["id"]

            if sensor_id not in self._runners:
                self._add_runner(sensor_id, sensor_data)
            else:
                pass

            return sensor_id

        except KeyError as e:
            logger.error(
                "Dados inválidos do sensor (campo ausente: %s) | data=%s",
                e,
                sensor_data,
            )
        except Exception as e:

            logger.error(
                "Erro inesperado ao processar sensor | data=%s",
                sensor_data,
            )
            logger.debug("Erro: %s", e)

        return None

    def _add_runner(self, sensor_id: int, sensor_data: dict):
        logger.info("Adicionando runner para sensor %s", sensor_id)

        sensor = sensor_creator.create(sensor_data)
        runner = SensorRunner(sensor, self._publisher)
        self._runners[sensor_id] = runner
        runner.start()

    def _update_runner(self, sensor_id: int, sensor_data: dict):
        self._runners[sensor_id].update(**sensor_data.get("parameters", {}))
        logger.debug(
            "Sensor %s atualizado: %s",
            sensor_id,
            sensor_data.get("parameters"),
        )

    def _remove_stale_runners(self, active_ids: set):
        stale_ids = set(self._runners.keys()) - active_ids
        for sensor_id in stale_ids:
            logger.info("Sensor %s removido da API — encerrando runner", sensor_id)
            self._runners.pop(sensor_id).stop()


sensor_pool = SensorPool()