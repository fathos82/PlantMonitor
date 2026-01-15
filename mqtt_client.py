import json
from datetime import datetime, timezone

from paho import mqtt
from paho.mqtt.client import Client

from logs import get_logger
from sensors.sensors import AbstractSensor
from settings import MQTT_ADDRESS

client = Client()
TOPIC = "plant/data"
PORT = 1883
KEEPALIVE = 80
logger = get_logger("SYSTEM")

def connect():
    logger.info("Inicializando conexão com servidor mqtt.")
    logger.debug("Conectando ao MQTT broker (%s:%s)...", MQTT_ADDRESS, PORT)

    try:
        client.connect(MQTT_ADDRESS, PORT, KEEPALIVE)
    except Exception:
        logger.critical(
            "Erro ao conectar ao broker MQTT (%s:%s)",
            MQTT_ADDRESS,
            PORT
        )
        raise SystemExit(1)



def send_data(data, sensor:AbstractSensor):
    try:
        map_data = {
            "sensorId": sensor.api_id,
            "capabilities": sensor.capabilities_values
            **data
        }

        logger.debug(map_data)
        payload = json.dumps(map_data)
        print(payload)
        logger.info("Sending data to MQTT: %s", str(payload))
        logger.debug("Sending data: %s", str(payload))
        client.publish(TOPIC, payload)
    except Exception as e:
        print(e)
