from typing import Dict

from api import client as api_client
from logs import get_logger
from sensors.drivers.hcsr04 import HCSR04DistanceSensor
from sensors.factory import sensor_factory
from sensors.base import AbstractSensor, SensorModel

logger = get_logger("SENSOR_POOL")


class SensorPool:
    def __init__(self):
        self.sensors_to_update = []
        self.sensors_to_remove = []
        self.sensors_to_add = []

        self.sensors_map: Dict[int, AbstractSensor] = {}
        self._register_drivers()

    def _register_drivers(self):
        sensor_factory.register(SensorModel.HC_SR04, HCSR04DistanceSensor)
        logger.debug("Sensor HC_SR04 registrado no factory")

    def discover(self, device_uuid: str):
        logger.info("Descoberta de sensores iniciada")

        sensors_data = api_client.get_sensors(device_uuid)

        if not sensors_data:
            logger.info("Nenhum sensor descoberto")
            return

        for sensor_data in sensors_data:
            self._process_sensor_data(sensor_data)

    def _process_sensor_data(self, sensor_data: dict):
        try:
            sensor_id = sensor_data["id"]

            if sensor_id not in self.sensors_map:
                logger.info("Novo sensor detectado (id=%s)", sensor_id)

                sensor_instance = sensor_factory.create(sensor_data)

                if sensor_instance.probe():
                    self.sensors_map[sensor_id] = sensor_instance
                    self.sensors_to_add.append(sensor_id)
                    logger.info("Sensor %s adicionado ao pool", sensor_id)
                else:
                    logger.warning(
                        "Sensor %s não respondeu ao probe",
                        sensor_id
                    )
            else:
                self.sensors_to_update.append(sensor_id)
                self.sensors_map[sensor_id].set_params(
                    **sensor_data.get("parameters", {})
                )
                logger.debug(
                    "Parâmetros atualizados para o sensor %s: %s",
                    sensor_id,
                    sensor_data.get("parameters")
                )

        except KeyError as e:
            logger.error(
                "Dados inválidos do sensor (campo ausente: %s) | data=%s",
                e,
                sensor_data
            )

        except Exception:
            logger.error(
                "Erro inesperado ao processar sensor | data=%s",
                sensor_data
            )

    def clear(self):
        for sensor_id in self.sensors_to_remove.copy():
            if sensor_id in self.sensors_map:
                self.sensors_map.pop(sensor_id)
                logger.info("Sensor %s removido do pool", sensor_id)

        self.sensors_to_remove.clear()
        self.sensors_to_add.clear()
        self.sensors_to_update.clear()

    @property
    def sensors(self):
        return self.sensors_map.values()


sensor_pool = SensorPool()