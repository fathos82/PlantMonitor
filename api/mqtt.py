import paho.mqtt.client as mqtt
from paho.mqtt.properties import Properties
from paho.mqtt.packettypes import PacketTypes

from logs import get_logger
from settings import MQTT_ADDRESS

MQTT_PORT = 1883
MQTT_KEEPALIVE = 80
MQTT_MESSAGE_EXPIRY_INTERVAL = 2 * 60 * 60

logger = get_logger("MQTT")


class MqttClient:

    def __init__(self):
        self._client = None
        self._topic_aliases: dict[str, int] = {}
        self._next_alias = 1

    def connect(self, client_id: str):
        logger.info("Inicializando conexão com broker MQTT")
        logger.debug("Conectando ao MQTT broker (%s:%s)...", MQTT_ADDRESS, MQTT_PORT)

        try:
            self._client = mqtt.Client(
                client_id=client_id,
                protocol=mqtt.MQTTv5,
            )
            self._client.connect(MQTT_ADDRESS, MQTT_PORT, MQTT_KEEPALIVE)
            self._client.loop_start()
        except Exception:
            logger.critical("Erro ao conectar ao broker MQTT (%s:%s)", MQTT_ADDRESS, MQTT_PORT)
            raise SystemExit(1)

    def publish(self, topic: str, payload: bytes, qos: int = 1):
        try:
            resolved_topic, alias = self._resolve_alias(topic)

            properties = Properties(PacketTypes.PUBLISH)
            properties.MessageExpiryInterval = MQTT_MESSAGE_EXPIRY_INTERVAL
            properties.TopicAlias = alias

            logger.debug("Publicando em %s (%d bytes)", topic, len(payload))

            self._client.publish(
                resolved_topic,
                payload,
                qos=qos,
                properties=properties,
            )
        except Exception as e:
            logger.debug("Erro ao publicar em %s (%s)", topic, e)

    def _resolve_alias(self, topic: str) -> tuple[str, int]:
        if topic not in self._topic_aliases:
            self._topic_aliases[topic] = self._next_alias
            self._next_alias += 1
            return topic, self._topic_aliases[topic]
        return "", self._topic_aliases[topic]


mqtt_client = MqttClient()