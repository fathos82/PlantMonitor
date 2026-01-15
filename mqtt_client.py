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

def connect():
    get_logger("SYSTEM").info("Connecting to MQTT broker...")
    result = client.connect(MQTT_ADDRESS, PORT, 60)

    if result == 0:
        print("Conectado com sucesso ao broker MQTT")
    else:
        print(f"Erro ao conectar. Código: {result}")



def send_data(data, sensor:AbstractSensor):
    try:
        dt = datetime.now(timezone.utc)
        timestamp = dt.isoformat().replace("+00:00", "Z")

        map_data = {
            "type": "distance",
            "unit": "celsius",
            "value": data["distance_cm"],
            "sensorId": sensor.api_id,
            "measuredAt": str(timestamp)
        }

        payload = json.dumps(map_data)
        client.publish(TOPIC, payload)
    except Exception as e:
        print(e)
