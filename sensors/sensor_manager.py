from typing import List

from sensors.distance_sensor import HCSR04DistanceSensor
from sensors.sensors import AbstractSensor
from utils import register_sensor_on_api
from settings import log, LogLevel, LogContext


class SensorPool:
    def __init__(self):
        self.sensors: List[AbstractSensor] = []

    def __automatic_scan_sensors(self):
        log("Varredura automática iniciada", context=LogContext.SENSOR)

        drives: List[AbstractSensor] = [
            HCSR04DistanceSensor()
        ]

        for sensor in drives:
            sensor_name = sensor.__class__.__name__
            try:
                if sensor.probe():
                    self.sensors.append(sensor)
                    log(f"Sensor detectado: {sensor_name}", context=LogContext.SENSOR)
                else:
                    log(f"Sensor ignorado: {sensor_name}", level=LogLevel.WARNING, context=LogContext.SENSOR)
            except Exception as e:
                log(f"Erro no probe ({sensor_name}): {e}", level=LogLevel.ERROR, context=LogContext.SENSOR)

        log(f"Varredura concluída ({len(self.sensors)} sensor(es))", context=LogContext.SENSOR)

    def discover(self, device_uuid):
        log("Descoberta de sensores iniciada", context=LogContext.SENSOR)

        self.__automatic_scan_sensors()

        if not self.sensors:
            log("Nenhum sensor encontrado", level=LogLevel.WARNING, context=LogContext.SENSOR)
            return

        for sensor in self.sensors:
            sensor_name = sensor.__class__.__name__
            try:
                 json = register_sensor_on_api(
                    sensor_name=sensor_name,
                    device_uuid=device_uuid,
                    capabilities=sensor.capabilities
                )
                 sensor.api_id = json['id']

            except Exception as e:
                # todo: o que deve acontecer caso não consiga registrar sensor
                log(f"Erro ao registrar sensor ({sensor_name}): {e}", level=LogLevel.ERROR, context=LogContext.API)
