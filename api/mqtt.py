import json
from logs import get_logger
from sensors.base import AbstractSensor
from settings import MQTT_ADDRESS

# IMPORTANTE: Importar o módulo principal para aceder à constante da versão 5
import paho.mqtt.client as mqtt
from paho.mqtt.properties import Properties
from paho.mqtt.packettypes import PacketTypes

# 1. CORREÇÃO: Forçar a versão 5 do protocolo!
client = mqtt.Client(protocol=mqtt.MQTTv5)

MQTT_PORT = 1883
MQTT_KEEPALIVE = 80
logger = get_logger("SYSTEM")


def connect():
    logger.info("Inicializando conexão com servidor mqtt.")
    logger.debug("Conectando ao MQTT broker (%s:%s)...", MQTT_ADDRESS, MQTT_PORT)

    try:
        client.connect(MQTT_ADDRESS, MQTT_PORT, MQTT_KEEPALIVE)
        client.loop_start()
    except Exception:
        logger.critical("Erro ao conectar ao broker MQTT (%s:%s)", MQTT_ADDRESS, MQTT_PORT)
        raise SystemExit(1)


def send_data(data, sensor: AbstractSensor):
    try:
        for capability in sensor.capabilities:
            if capability in data:
                # Arredondando o valor para evitar "ruído" decimal pesado
                value = round(data[capability], 2)

                # 2. OTIMIZAÇÃO: JSON super enxuto (ID e Tipo saíram daqui)
                map_data = {
                    "measuredAt": data["measuredAt"],
                    "value": value
                }

                # O ID e o Tipo agora vivem apenas na rota
                # topic = f"pm/s/{sensor.api_id}/c/{capability}"
                topic = "plant/data"
                payload = json.dumps(map_data)

                # 3. CORREÇÃO: Configurar as propriedades do MQTT 5
                properties = Properties(PacketTypes.PUBLISH)
                properties.MessageExpiryInterval = 60 * 60 * 2  # Expira em 2 horas

                logger.debug("Sending data to %s: %s", topic, str(payload))

                # UNIFICAÇÃO: Apenas UM publish com tudo o que tem direito!
                client.publish(
                    topic,
                    payload,
                    qos=1,  # Garante a entrega na fila
                    retain=True,  # Guarda a última leitura para novos frontends
                    properties=properties  # Define a validade de 2h
                )

    except Exception as e:
        logger.error("Error sending data: %s", str(e))