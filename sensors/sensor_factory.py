from sensors.sensors import SensorModel
from settings import log


class SensorFactory:

    _REGISTRY = {}

    def register(self, sensor_type: SensorModel, sensor_cls):
        self._REGISTRY[sensor_type] = sensor_cls

    def create(self, sensor_data: dict):
        #todo: talvez futuramente reportar esse error para api!
        #todo: associar erro ao sensor solicitado pelo ID
        try:
            sensor_type = SensorModel(sensor_data["model"])
        except ValueError:
            log(f"Modelo inválido recebido da API: {sensor_data['model']}", level="error")

        if sensor_type not in self._REGISTRY:
            log(f"Sensor não suportado: {sensor_type}", level="error")
        sensor_cls = self._REGISTRY[sensor_type]
        sensor = sensor_cls(**sensor_data.get("parameters", {}))
        sensor.api_id = sensor_data.get("id")
        return sensor

sensor_factory = SensorFactory()