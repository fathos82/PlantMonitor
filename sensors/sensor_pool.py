from typing import List, Dict

from sensors.distance_sensor import HCSR04DistanceSensor
from sensors.sensor_factory import sensor_factory
from sensors.sensors import AbstractSensor
from utils import register_sensor_on_api, get_sensors_from_api_by_device_uuid
from settings import log, LogLevel, LogContext
from sensors.sensors import SensorModel

class SensorPool:
    def __init__(self):
        self.sensors_to_update = []
        self.sensors_to_remove = []
        self.sensors_to_add = []

        self.sensors_map: Dict[int, AbstractSensor] = {}
        self.register_sensors_to_factory()
    def register_sensors_to_factory(self):
        sensor_factory.register(SensorModel.HC_SR04, HCSR04DistanceSensor)

    def __automatic_scan_sensors(self):
        log("Varredura automática iniciada", context=LogContext.SENSOR)

        drives: List[AbstractSensor] = [
            HCSR04DistanceSensor()
        ]
        sensors: List[AbstractSensor] = []

        for sensor in drives:
            sensor_name = sensor.__class__.__name__
            try:
                if sensor.probe():
                    sensors.append(sensor)
                    log(f"Sensor detectado: {sensor_name}", context=LogContext.SENSOR)
                else:
                    log(f"Sensor ignorado: {sensor_name}", level=LogLevel.WARNING, context=LogContext.SENSOR)
            except Exception as e:
                log(f"Erro no probe ({sensor_name}): {e}", level=LogLevel.ERROR, context=LogContext.SENSOR)

        log(f"Varredura concluída ({len(self.sensors_map)} sensor(es))", context=LogContext.SENSOR)
        return sensors

    def _fetch_sensors_from_api(self, device_uuid):
        try:
            return get_sensors_from_api_by_device_uuid(device_uuid, None)
        except Exception as e:
            log(
                f"Erro ao buscar sensores da API: {e}",
                level=LogLevel.ERROR,
                context=LogContext.SENSOR
            )
            return []


    def discover(self, device_uuid):
        # todo: add locks

        log("Descoberta de sensores iniciada", context=LogContext.SENSOR)
        sensors_from_api_data = self._fetch_sensors_from_api(device_uuid)

        # todo: add logs
        for sensor_data in sensors_from_api_data:
            self._process_sensor_data(sensor_data)




    def _process_sensor_data(self, sensor_data):
        try:
            sensor_id = sensor_data['id']

            if sensor_id not in self.sensors_map:
                sensor_instance = sensor_factory.create(sensor_data)

                if sensor_instance.probe():
                    self.sensors_map[sensor_id] = sensor_instance
                    self.sensors_to_add.append(sensor_id)
                else:
                    log(f"Sensor {sensor_id} não respondeu ao probe",level=LogLevel.WARNING, context=LogContext.SENSOR)
            else:
                self.sensors_to_update.append(sensor_id)
                print("SETANDO PARAMETROS")
                self.sensors_map[sensor_id].set_params(**sensor_data["params"])

        except KeyError as e:
            log(f"Dados inválidos do sensor (campo ausente): {e} | data={sensor_data}",level=LogLevel.ERROR,context=LogContext.SENSOR)

        except Exception as e:
            log(f"Erro inesperado ao processar sensor {sensor_data}: {e}",level=LogLevel.ERROR,context=LogContext.SENSOR)

    def clear(self):
        for s in self.sensors_to_remove.copy():
            if s in self.sensors_map:
                self.sensors_map.pop(s)
        self.sensors_to_remove = []
        self.sensors_to_add = []
        self.sensors_to_update = []

    @property
    def sensors(self):
        return self.sensors_map.values()

sensor_pool = SensorPool()