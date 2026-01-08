from sensors.sensor_runner import SensorRunner, Command
from sensors.sensors import AbstractSensor


class ThreadSupervisor:
    def __init__(self):
        self.runners = {}

    def add_sensor(self, sensor:AbstractSensor):
        print("Adding sensor {}".format(sensor.sensor_name))
        print("Sensor ID: {}".format(sensor.api_id))
        runner = SensorRunner(sensor)
        self.runners[sensor.local_id] = runner
        runner.start()
        runner.commands.put(Command.START)

    def remove_sensor(self, local_id):
        runner = self.runners.pop(local_id, None)
        if runner:
            runner.commands.put(Command.STOP)

    def reload_sensor(self, sensor):

        runner = self.runners.get(sensor.api_id)
        print("RUNNER COLETADO: ", runner)
        if runner:
            runner.commands.put(Command.RELOAD)

thread_supervisor = ThreadSupervisor()