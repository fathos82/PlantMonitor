import json
import os
import socket
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
import paho.mqtt.client as mqtt
import segno

from sensors.sensors import AbstractSensor



def register_or_get_device():
    DEVICE_UUID_FILE = os.path.expanduser("~/.plantmonitor/device_id")
    context = "DEVICE"
    url = "http://192.168.0.107:8080/api/devices/"
    # todo: data get para verificar se foi mesmo salvo!
    log("Verificando se o dispositivo já está registrado", context=context)

    path = Path(DEVICE_UUID_FILE)

    if path.exists():
        device_uuid = path.read_text().strip()
        log(
            f"Dispositivo já registrado anteriormente (ID: {device_uuid})",
            context=context
        )
        return device_uuid

    log(
        "Dispositivo não encontrado. Iniciando novo registro",
        level="warning",
        context=context
    )

    os.makedirs(os.path.dirname(DEVICE_UUID_FILE), exist_ok=True)

    device_uuid = str(uuid.uuid4())


    log(
        f"Identificador único do dispositivo gerado: {device_uuid}",
        context=context
    )

    payload = {
        "deviceUid": device_uuid,
        "deviceType": "raspberrypi",
        "name": "Sem Nome",  # TODO: tornar configurável
        "hostname": socket.gethostname(),
    }

    log("Enviando dados do dispositivo para a API", context=context)

    try:
        response = requests.post(url, json=payload, timeout=5)

        if response.status_code in (200, 201):
            log(
                "Dispositivo registrado com sucesso na API",
                context=context
            )
            path.write_text(device_uuid)
        else:
            log(
                f"API respondeu com erro ({response.status_code}): {response.text}",
                level="error",
                context=context
            )

    except requests.exceptions.RequestException as e:
        log(
            f"Falha ao comunicar com a API: {e.__cause__}",
            level="critical",
            context=context
        )


    return device_uuid



import requests
from settings import log, LogLevel, LogContext


def register_sensor_on_api(sensor_name, capabilities, device_uuid):
    url = "http://192.168.0.107:8080/api/sensors/"

    log(f"Registrando sensor {sensor_name}", context=LogContext.API)

    payload = {
        "deviceUuId": device_uuid,
        "sensorName": sensor_name,
        "capabilities": capabilities,
    }

    try:
        print(payload)
        response = requests.post(url, json=payload, timeout=5)

        if response.status_code in (200, 201):
            log(f"Sensor registrado: {sensor_name}", context=LogContext.API)
            return response.json()

        log(
            f"Falha ao registrar sensor {sensor_name} (HTTP {response.status_code})",
            level=LogLevel.ERROR,
            context=LogContext.API
        )
        return None

    except requests.exceptions.RequestException as e:
        log(
            f"Erro ao registrar sensor {sensor_name}: {e}",
            level=LogLevel.ERROR,
            context=LogContext.API
        )
        return None

    # todo: add logs response


def generate_qrcode_to_set_account(device_uuid):
    data = "plantmonitor://pair?token=" + device_uuid
    qr = segno.make(data)
    qr.terminal(border=2, compact=True)
    while True:  # todo: verify is_confirmed
        time.sleep(1)


BROKER = "192.168.0.107"
PORT = 1883
TOPIC = "plant/data"

client = mqtt.Client()
client.connect(BROKER, PORT, 60)




def get_sensors_from_api_by_device_uuid(device_uuid, since):
    url = "http://192.168.0.107:8080/api/sensors/"
    # todo: add logs
    response = requests.get(url, params={"deviceUid": device_uuid})
    print(response)
    if response.status_code in (200, 201):
        return response.json()

    return None

def send_data(data, sensor:AbstractSensor):
    try:
        dt = datetime.now(timezone.utc)
        timestamp = dt.isoformat().replace("+00:00", "Z")
        map_data = {
            "type": "distance",
            "unit": "celsius",
            "value": data[0],
            "sensorId": sensor.api_id,
            "measuredAt": str(timestamp)
        }
        payload = json.dumps(map_data)
        client.publish(TOPIC, payload)

        print("sending data via mqtt:", payload)
    except Exception as e:
        print(e)
