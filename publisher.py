import time
from typing import Dict, List, Iterator, Any

from api.mqtt import MqttClient
from filters import Filter
from logs import get_logger
from sensors.base import AbstractSensor
from sensors.sensor_data_pb2 import SensorReadingBatch

logger = get_logger("PUBLISHER")

BATCH_SIZE = 10


# TODO: Replacte this pattern
class Publisher:

    def __init__(self, client: MqttClient, device_uuid: str):
        self._client = client
        self._device_uuid = device_uuid
        self.filters:List[Filter] = []
        self.batches: Dict[str, SensorReadingBatch] = {}

    def add_filter(self, filter: Filter) -> None:
        self.filters.append(filter)
    def publish(self, data: dict, sensor: AbstractSensor):
        try:
            for capability in sensor.capabilities:
                if capability not in data:
                    continue

                topic = self._build_topic(sensor, capability.name)

                if topic not in self.batches:
                    batch = SensorReadingBatch()
                    batch.base_timestamp = int(time.time() * 1000)
                    self.batches[topic] = batch
                batch = self.batches[topic]
                sensor_read = batch.readings.add()

                valor = data.get(capability)
                valor = round(valor, 2)
                sensor_read.value = valor
                agora_ms = int(time.time() * 1000)
                sensor_read.delta_ms = agora_ms - batch.base_timestamp

                if len(batch.readings) >= BATCH_SIZE:
                    batch = self._apply_filters(batch)
                    logger.debug("Publishing topic %s", topic)
                    payload = batch.SerializeToString()
                    self._client.publish(topic, payload)
                    logger.debug("Publicado em %s (%d bytes)", topic, len(payload))
                    del self.batches[topic]

        except Exception:
            logger.exception("Erro ao publicar leitura do sensor %s", sensor.api_id)

    def flush(self):
        """Força o envio de todos os lotes incompletos antes de desligar o programa."""
        try:
            # list() é necessário para congelar as chaves, pois vamos modificar o dicionário
            for topic in list(self.batches.keys()):
                batch = self.batches[topic]

                if len(batch.readings) > 0:
                    payload = batch.SerializeToString()
                    self._client.publish(topic, payload)
                    logger.debug("Flush efetuado: Publicado em %s (%d bytes)", topic, len(payload))

            self.batches.clear()
            logger.info("Flush de dados MQTT finalizado com sucesso.")

        except Exception:
            logger.exception("Erro crítico ao tentar fazer o flush dos dados MQTT")

    def _build_topic(self, sensor: AbstractSensor, capability: str) -> str:
        return f"plant_monitor/{sensor.api_id}/{capability}"

    def _apply_filters(self, batch:SensorReadingBatch) -> SensorReadingBatch:
        for reading in batch.readings:
            for f in self.filters:
                reading.value = f.filter(reading.value)
        return batch