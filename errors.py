


class SensorError(Exception):
    def __init__(self,*args, **kwargs):
        super().__init__( *args, *kwargs)
        self.sensor_id = kwargs.get('sensor_id')

class SensorSetupError(SensorError):
    pass
class SensorTimeoutError(SensorError):
    pass
