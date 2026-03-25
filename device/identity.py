import os
import socket
import uuid
from pathlib import Path

from api import client as api_client
from logs import get_logger

logger = get_logger("DEVICE")

_DEVICE_UUID_FILE = os.path.expanduser("~/.plantmonitor/device_id")


def load_or_create() -> str:
    """
    Retorna o UUID do device.
    Se já existir localmente, apenas lê e retorna.
    Se for novo, gera, registra na API e persiste localmente.
    """
    path = Path(_DEVICE_UUID_FILE)

    if path.exists():
        device_uuid = path.read_text().strip()
        logger.info("Dispositivo já registrado (uuid=%s)", device_uuid)
        return device_uuid

    return _register_new_device(path)


def _register_new_device(path: Path) -> str:
    """
    Gera um novo UUID, registra na API e salva localmente.
    """
    logger.warning("Dispositivo não encontrado. Iniciando novo registro")

    device_uuid = str(uuid.uuid4())
    logger.debug("UUID gerado: %s", device_uuid)

    payload = {
        "deviceUid": device_uuid,
        "deviceType": "raspberrypi",
        "name": "Sem Nome",  # TODO: tornar configurável via settings
        "hostname": socket.gethostname(),
    }
    print(payload)

    api_client.register_device(device_uuid, payload)

    os.makedirs(path.parent, exist_ok=True)
    path.write_text(device_uuid)
    logger.info("UUID persistido localmente")

    return device_uuid