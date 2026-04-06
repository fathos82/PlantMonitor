import os
import socket
import uuid
from pathlib import Path

from api import client as api_client
from device_info import DeviceInfo
from logs import get_logger

logger = get_logger("DEVICE")

_DEVICE_UUID_FILE = os.path.expanduser("~/.plantmonitor/device_id")


def load_or_create() -> DeviceInfo:
    """
    Garante que o device esteja registrado na API.

    Fluxo:
    - se existir UUID local, valida na API;
    - se a API disser que não existe, registra novamente com o mesmo UUID;
    - se não existir UUID local, gera um novo, registra e persiste.
    """
    path = Path(_DEVICE_UUID_FILE)
    print(path)
    if path.exists():
        device_uuid = path.read_text().strip()

        if device_uuid:
            try:
                response = api_client.get_device(device_uuid)
                print(response)
                logger.info("Dispositivo já registrado (uuid=%s)", device_uuid)
                return DeviceInfo(device_uuid, response["id"], response["name"])
            except Exception:
                logger.warning(
                    "UUID local encontrado, mas não existe na API. Re-registrando (uuid=%s)",
                    device_uuid,
                )

                payload = {
                    "deviceUid": device_uuid,
                    "deviceType": "raspberrypi",
                    "name": "Sem Nome",
                    "hostname": socket.gethostname(),
                }

                response = api_client.register_device(device_uuid, payload)
                logger.info("UUID re-registrado na API (uuid=%s)", device_uuid)
                return DeviceInfo(uuid, response["id"], response["name"])

    device_uuid = str(uuid.uuid4())
    logger.warning("Dispositivo não encontrado. Criando novo registro (uuid=%s)", device_uuid)

    payload = {
        "deviceUid": device_uuid,
        "deviceType": "raspberrypi",
        "name": "Sem Nome",
        "hostname": socket.gethostname(),
    }

    response = api_client.register_device(device_uuid, payload)

    os.makedirs(path.parent, exist_ok=True)
    path.write_text(device_uuid)

    logger.info("UUID persistido localmente")
    return DeviceInfo(uuid, response["id"], response["name"])
