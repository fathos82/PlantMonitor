import json
import os
import socket
import time
import uuid
from pathlib import Path

import paho.mqtt.client as mqtt
import requests
import segno


def get_or_create_device_id():
    DEVICE_ID_FILE = "/etc/plantmonitor"
    path = Path(DEVICE_ID_FILE)
    if path.exists():
        return path.read_text().strip()
    os.makedirs(os.path.dirname(DEVICE_ID_FILE), exist_ok=True)
    device_id = str(uuid.uuid4())
    path.write_text(device_id)
    return device_id




def register_device():
    print("registering device on api")
    print("generating uuid device: ")
    # todo: verifica se ja não existe registro
    uuid = get_or_create_device_id()
    print("uuid: ", uuid)
    payload = {
        "deviceUid": uuid,
        "deviceType": "raspberrypi",
        "name": "Sem Nome", # todo: alterar isso
        "hostname":  socket.gethostname(),
    }
    url = 'http://192.168.0.107:8080/api/devices/'
    response = requests.post(url, json=payload)
    return uuid



def generate_qrcode_to_set_account(device_uuid):
    data = "plantmonitor://pair?token="+device_uuid
    qr = segno.make(data)
    qr.terminal(border=2, compact=True)
    while True:# todo: verify is_confirmed
        time.sleep(1)



BROKER = "192.168.0.107"
PORT = 1883
TOPIC = "teste/topico"

client = mqtt.Client()
client.connect(BROKER, PORT, 60)

def send_data(data):
    payload = json.dumps(data)
    client.publish(TOPIC, payload)
    print("sending data via mqtt:", payload)




