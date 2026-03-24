from sensors.base import SensorModel

class SensorCreator:
    def __init__(self):
        self._registry = {}

    def register(self, sensor_type: SensorModel, sensor_cls):
        self._registry[sensor_type] = sensor_cls

    def create(self, sensor_data: dict):
        try:
            sensor_type = SensorModel(sensor_data["model"])
        except ValueError:
            raise ValueError(f"Modelo inválido recebido da API: {sensor_data['model']}")

        if sensor_type not in self._registry:
            raise ValueError(f"Sensor não suportado: {sensor_type}")

        sensor_cls = self._registry[sensor_type]
        sensor = sensor_cls(**sensor_data.get("parameters", {}))
        sensor.api_id = sensor_data.get("id")
        return sensor


sensor_creator = SensorCreator()