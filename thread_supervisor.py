from sensors.sensor_runner import SensorRunner, Command
from sensors.sensors import AbstractSensor


class ThreadSupervisor:
    def __init__(self):
        self.runners = {}

    def add_sensor(self, sensor:AbstractSensor):
        runner = SensorRunner(sensor)
        self.runners[sensor.api_id] = runner
        runner.start()
        runner.commands.put(Command.START)

    def remove_sensor(self, sensor):
        runner = self.runners.pop(sensor.api_id, None)
        if runner:
            runner.commands.put(Command.STOP)

    def reload_sensor(self, sensor, params):

        runner = self.runners.get(sensor.api_id)
        if runner:
            runner.commands.put(Command.RELOAD)

thread_supervisor = ThreadSupervisor()