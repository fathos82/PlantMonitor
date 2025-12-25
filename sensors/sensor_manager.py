from typing import List

from sensors.sensor_test import SensorTest
from sensors.sensors import AbstractSensor


class SensorPool:
    def __init__(self):
        self.sensors = []

    def __automatic_scan_sensors(self):
        drives:List[AbstractSensor] = [SensorTest(), SensorTest(), SensorTest(), SensorTest()]
        for sensor in drives:
            if sensor.probe():
                self.sensors.append(sensor)
    def discover(self):
        self.__automatic_scan_sensors()
