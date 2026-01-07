from sensors.sensor_runner import SensorRunner, Command


class ThreadSupervisor:
    def __init__(self):
        self.runners = {}

    def add_sensor(self, sensor):
        runner = SensorRunner(sensor)
        self.runners[sensor.local_id] = runner
        runner.start()
        runner.commands.put(Command.START)

    def remove_sensor(self, local_id):
        runner = self.runners.pop(local_id, None)
        if runner:
            runner.commands.put(Command.STOP)

    def reload_sensor(self, local_id):
        runner = self.runners.get(local_id)
        if runner:
            runner.commands.put(Command.RELOAD)

thread_supervisor = ThreadSupervisor()