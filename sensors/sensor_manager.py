from typing import List, Dict

from sensors.distance_sensor import HCSR04DistanceSensor
from sensors.sensor_factory import sensor_factory
from sensors.sensors import AbstractSensor
from utils import register_sensor_on_api, get_sensors_from_api_by_device_uuid
from settings import log, LogLevel, LogContext
from sensors.sensors import SensorModel

class SensorPool:
    def __init__(self):
        self.sensors: Dict[int, AbstractSensor] = {}
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

        log(f"Varredura concluída ({len(self.sensors)} sensor(es))", context=LogContext.SENSOR)
        return sensors
    def get_sensors_from_api(self, device_uuid, since=None):
        # todo: add logs
        sensors = []
        result = get_sensors_from_api_by_device_uuid(device_uuid, since)
        print("RESULTADOS: ", result)
        for sensor in result:
            try:
                print("SENSOR: ", sensor)
                sensors.append(sensor_factory.create(sensor))
            except Exception as e:
                #todo: logs
                pass
        print(sensors)
        return sensors

    def discover(self, device_uuid):
        # todo: add locks

        log("Descoberta de sensores iniciada", context=LogContext.SENSOR)
        possible_new_sensors = []
        possible_new_sensors.extend(self.__automatic_scan_sensors())

        registered_sensors = []
        registered_sensors.extend(self.get_sensors_from_api(device_uuid))

        if not self.sensors:
            log("Nenhum sensor encontrado", level=LogLevel.WARNING, context=LogContext.SENSOR)
            return

        for sensor in possible_new_sensors:
            sensor_name = sensor.__class__.__name__
            try:
                json = register_sensor_on_api(
                    sensor_name=sensor_name,
                    device_uuid=device_uuid,
                    capabilities=sensor.capabilities
                )
                # todo: cuidado, rever isso, pq mexer aqui ira mexer em um looping em execução
                sensor.api_id = json['id']
                self.sensors[sensor.api_id] = sensor


            except Exception as e:
                    # todo: o que deve acontecer caso não consiga registrar sensor
                            log(f"Erro ao registrar sensor ({sensor_name}): {e}", level=LogLevel.ERROR, context=LogContext.API)

        # todo: add logs
        for sensor in registered_sensors:
            self.sensors[sensor.api_id] = sensor
