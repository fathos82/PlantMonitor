import json
import os
import socket
import time
import uuid
from pathlib import Path
import segno

from logs import get_logger


def register_or_get_device():
    logger = get_logger("DEVICE")
    DEVICE_UUID_FILE = os.path.expanduser("~/.plantmonitor/device_id")
    url = "http://192.168.0.117:8080/api/devices/"
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
        response = requests.post(url, json=payload, timeout=5)

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
    url = "http://192.168.0.117:8080/api/sensors/"
    # todo: add logs
    response = requests.get(url, params={"deviceUid": device_uuid})

    if response.status_code in (200, 201):
        return response.json()

    return None

import requests
#
# def send_to_api_error(message, sensor_id):
#     url = f"http://192.168.0.117:8080/api/sensors/{sensor_id}/errors/"
#     data = {"message": message}
#
#     try:
#         response = requests.post(url, json=data, timeout=5)
#
#         if response.ok:
#             log(f"Erro do sensor enviado com sucesso (sensor_id={sensor_id})", level=LogLevel.INFO,
#                 context=LogContext.API)
#         else:
#             log(f"Falha ao enviar erro do sensor "f"(sensor_id={sensor_id}, status={response.status_code})",
#                 level=LogLevel.ERROR, context=LogContext.API)
#
#     except RequestException as e:
#         # engloba Timeout, ConnectionError, etc
#         log(
#             f"Falha ao enviar erro do sensor para API "
#             f"(sensor_id={sensor_id}): {e}",
#             level=LogLevel.WARNING,
#             context=LogContext.API
#         )

