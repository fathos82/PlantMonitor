import socket
import uuid
from pathlib import Path
import requests

DEVICE_ID_FILE = "/etc/plantmonitor/device_id"

def get_or_create_device_id():
    path = Path(DEVICE_ID_FILE)
    if path.exists():
        return path.read_text().strip()

    device_id = str(uuid.uuid4())
    path.write_text(device_id)
    return device_id




def register_device():
    print("registering device on api")
    payload = {
        "deviceUid": get_or_create_device_id(),
        "name": "Sem Nome",
        "hostname":  socket.gethostname(),
    }
    url = 'http://192.168.0.107:8080/api/device/register'
    response = requests.get(url)
    pass




def automatic_read_sensors():
    pass

def register_sensor(sensor):
    pass



