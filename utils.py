import json
import os
import socket
import uuid
from pathlib import Path
import requests
import qrcode


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



def generate_qrcode(device_uuid):
    data = "plantmonitor://pair?token="+device_uuid
    qr = qrcode.QRCode(
        version=1,
        box_size=1,
        border=1,
    )
    qr.add_data(data)
    qr.make(fit=True)

    qr.print_ascii(invert=True)


def automatic_read_sensors():
    pass

def register_sensor(sensor):
    pass



