import  paho.mqtt.client as mqtt
import random
import time
import json

client = mqtt.Client()
# client.connect("localhost", 1883, 60)

valor = 25.0

while True:
    valor += random.uniform(-0.2, 0.2)
    payload = {
        "sensor_id": "temp_01",
        "value": round(valor, 2),
        "unit": "C"
    }
    print(payload)
    #
    # client.publish("sensores/temperatura", json.dumps(payload))
    # time.sleep(1)
