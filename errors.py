

class SensorError(Exception):
    def __init__(self, message: str, sensor_id: int | None = None):
        self.message = message
        self.sensor_id = sensor_id
        super().__init__(message)  # ⚠️ apenas a mensagem
    def __str__(self):
        return self.message

class SensorSetupError(SensorError):
    pass
class SensorTimeoutError(SensorError):
    pass
