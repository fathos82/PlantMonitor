from sensors.base import AbstractSensor
from sensors.runner import SensorRunner, Command


class ThreadSupervisor:
    def __init__(self):
        self.runners = {}

    def add_sensor(self, sensor:AbstractSensor):
        runner = SensorRunner(sensor)
        self.runners[sensor.api_id] = runner
        runner.start()
        runner.commands.put(Command.START)

    def remove_sensor(self, sensor_id):
        runner = self.runners.pop(sensor_id, None)
        if runner:
            runner.commands.put(Command.STOP)

    def reload_sensor(self, sensor_id):
        runner = self.runners.get(sensor_id)
        if runner:
            runner.commands.put(Command.RELOAD)

thread_supervisor = ThreadSupervisor()