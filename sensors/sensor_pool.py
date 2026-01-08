from typing import List, Dict

from sensors.distance_sensor import HCSR04DistanceSensor
from sensors.sensor_factory import sensor_factory
from sensors.sensors import AbstractSensor
from utils import register_sensor_on_api, get_sensors_from_api_by_device_uuid
from settings import log, LogLevel, LogContext
from sensors.sensors import SensorModel

class SensorPool:
    def __init__(self):
        self.sensors_to_remove = []
        self.sensors_to_add = []
        self.sensor_to_update = []

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
    def get_sensors_from_api(self, device_uuid, since=None):
        # todo: add logs
        sensors = []
        result = get_sensors_from_api_by_device_uuid(device_uuid, since)
        for sensor in result:
            try:
                sensors.append(sensor_factory.create(sensor))
            except Exception as e:
                #todo: logs
                pass
        return sensors
    @property
    def sensors(self):
        return self.sensors_map.values()
    def discover(self, device_uuid):
        # todo: add locks

        log("Descoberta de sensores iniciada", context=LogContext.SENSOR)
        registered_sensors = []
        registered_sensors.extend(self.get_sensors_from_api(device_uuid))
        # todo: add logs
        keys = self.sensors_map.keys()
        for sensor in registered_sensors:
            if sensor.probe():
                if sensor.api_id in keys:
                    self.sensor_to_update.append(sensor)
                else:
                    self.sensors_to_add.append(sensor)
                    self.sensors_map[sensor.api_id] = sensor




        if not self.sensors_map:
            log("Nenhum sensor encontrado", level=LogLevel.WARNING, context=LogContext.SENSOR)
            return
    def clear(self):
        print("PARA ATUALIZAR: ", self.sensor_to_update)
        for s in self.sensors_to_remove.copy():
            if s in self.sensors_map:
                self.sensors_map.pop(s)

        self.sensors_to_remove = []
        self.sensors_to_add = []
        self.sensor_to_update = []
sensor_pool = SensorPool()