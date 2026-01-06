from sensors.sensors import SensorModel


class SensorFactory:

    _REGISTRY = {}

    def register(self, sensor_type: SensorModel, sensor_cls):
        self._REGISTRY[sensor_type] = sensor_cls

    def create(self, sensor_data: dict):
        try:
            sensor_type = SensorModel(sensor_data["model"])
            print(sensor_type)
            print(sensor_type.name)
        except ValueError:
            raise ValueError(f"Modelo inválido recebido da API: {sensor_data['model']}")

        if sensor_type not in self._REGISTRY:
            raise ValueError(f"Sensor não suportado: {sensor_type}")
        sensor_cls = self._REGISTRY[sensor_type]
        sensor = sensor_cls(**sensor_data.get("parameters", {}))
        sensor.api_id = sensor_data.get("id")
        return sensor

sensor_factory = SensorFactory()