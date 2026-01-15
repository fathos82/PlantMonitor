import json
import os
import socket
import time
import uuid
from pathlib import Path
import segno
from requests import RequestException

from logs import get_logger
from mqtt_client import logger
from settings import DEVICE_API_URL, SENSOR_API_URL


def register_or_get_device():
    logger = get_logger("DEVICE")
    #todo: adicionar nome do device no log
    DEVICE_UUID_FILE = os.path.expanduser("~/.plantmonitor/device_id")
    # TODO: data get para verificar se foi mesmo salvo!

    logger.info("Verificando se o dispositivo já está registrado")

    path = Path(DEVICE_UUID_FILE)

    if path.exists():
        device_uuid = path.read_text().strip()
        logger.info(
            "Dispositivo já registrado anteriormente (ID: %s)",
            device_uuid
        )
        return device_uuid

    logger.warning("Dispositivo não encontrado. Iniciando novo registro")

    os.makedirs(os.path.dirname(DEVICE_UUID_FILE), exist_ok=True)

    device_uuid = str(uuid.uuid4())

    logger.info("Identificador único do dispositivo gerado: %s",device_uuid)

    payload = {
        "deviceUid": device_uuid,
        "deviceType": "raspberrypi",
        "name": "Sem Nome",  # TODO: tornar configurável
        "hostname": socket.gethostname(),
    }

    logger.info("Enviando dados do dispositivo para a API")

    try:
        response = requests.post(DEVICE_API_URL, json=payload, timeout=5)

        if response.status_code in (200, 201):
            logger.info("Dispositivo registrado com sucesso na API")
            path.write_text(device_uuid)
        else:
            logger.error(
                "API respondeu com erro (%s): %s",
                response.status_code,
                response.text
            )

    except requests.exceptions.RequestException:
        logger.exception("Falha ao comunicar com a API")
        raise SystemExit(1)

    return device_uuid





def generate_qrcode_to_set_account(device_uuid):
    data = "plantmonitor://pair?token=" + device_uuid
    qr = segno.make(data)
    qr.terminal(border=2, compact=True)
    while True:  # todo: verify is_confirmed
        time.sleep(1)








def get_sensors_from_api_by_device_uuid(device_uuid, since):
    logger = get_logger("SYSTEM")
    logger.debug(
        "Requisitando sensores da API",
        extra={
            "device_uuid": device_uuid,
            "since": since,
            "url": SENSOR_API_URL,
        }
    )

    try:
        response = requests.get(SENSOR_API_URL,params={"deviceUid": device_uuid},timeout=5)
        logger.debug("Resposta da API recebida",)
        if response.status_code in (200, 201):
            data = response.json()

            logger.debug("Sensores retornados com sucesso")

            return data

        logger.debug("API respondeu com status inesperado")

    except requests.exceptions.RequestException as e:
        logger.error("Falha na comunicação com a API")
    return None

import requests
def send_to_api_error(message, sensor_id):
    logger = get_logger("SYSTEM")
    url = f"http://192.168.0.117:8080/api/sensors/{sensor_id}/errors/"
    data = {"message": message}

    try:
        response = requests.post(url, json=data, timeout=5)

        if response.ok:
            logger.warning(f"Erro do sensor enviado com sucesso (sensor_id={sensor_id})")
        else:
            logger.error(f"Falha ao enviar erro do sensor "f"(sensor_id={sensor_id}, status={response.status_code})")
    except RequestException as e:
        # engloba Timeout, ConnectionError, etc
        logger.error(f"Falha ao enviar erro do sensor para API " f"(sensor_id={sensor_id}): {e}")

