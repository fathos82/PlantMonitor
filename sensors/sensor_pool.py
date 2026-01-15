from typing import List, Dict

from logs import get_logger
from sensors.distance_sensor import HCSR04DistanceSensor
from sensors.sensor_factory import sensor_factory
from sensors.sensors import AbstractSensor, SensorModel
from utils import get_sensors_from_api_by_device_uuid

logger = get_logger("SENSOR_POOL")


class SensorPool:
    def __init__(self):
        self.sensors_to_update = []
        self.sensors_to_remove = []
        self.sensors_to_add = []

        self.sensors_map: Dict[int, AbstractSensor] = {}
        self.register_sensors_to_factory()

    def register_sensors_to_factory(self):
        sensor_factory.register(SensorModel.HC_SR04, HCSR04DistanceSensor)
        logger.debug("Sensor HC_SR04 registrado no factory")

    def __automatic_scan_sensors(self) -> List[AbstractSensor]:
        logger.info("Varredura automática iniciada")

        drivers: List[AbstractSensor] = [
            HCSR04DistanceSensor()
        ]

        sensors: List[AbstractSensor] = []

        for sensor in drivers:
            sensor_name = sensor.__class__.__name__
            try:
                if sensor.probe():
                    sensors.append(sensor)
                    logger.info("Sensor detectado: %s", sensor_name)
                else:
                    logger.warning("Sensor ignorado: %s", sensor_name)
            except Exception:
                logger.exception("Erro durante probe do sensor %s", sensor_name)

        logger.info(
            "Varredura concluída (%d sensor(es) detectado(s))",
            len(sensors)
        )

        return sensors

    def _fetch_sensors_from_api(self, device_uuid):
        try:
            logger.debug("Buscando sensores da API (device_uuid=%s)", device_uuid)
            return get_sensors_from_api_by_device_uuid(device_uuid, None)
        except Exception:
            logger.exception("Erro ao buscar sensores da API")
            return []

    def discover(self, device_uuid):
        logger.info("Descoberta de sensores iniciada")

        sensors_from_api_data = self._fetch_sensors_from_api(device_uuid)

        for sensor_data in sensors_from_api_data:
            self._process_sensor_data(sensor_data)
        if len(sensors_from_api_data) != 0:
            logger.info("Nenhum sensor descoberto")
        return

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
            logger.exception(
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
