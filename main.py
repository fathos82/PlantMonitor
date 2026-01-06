import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from logging import CRITICAL

from sensors.sensor_manager import SensorPool
from sensors.sensors import AbstractSensor
from settings import log
from utils import register_or_get_device, generate_qrcode_to_set_account, send_data
SLEEP_TIME = 0.5
def run(sensor: AbstractSensor):
    while True:
        value = sensor.read()
        print(sensor.to_dict())

        dt = datetime.now(timezone.utc)
        timestamp = dt.isoformat().replace("+00:00", "Z")
        send_data(value,  sensor, timestamp)
        time.sleep(SLEEP_TIME)





def main():
    # todo: improve logs
    # todo: verify is exists qr code
    device_uuid = register_or_get_device()
    if device_uuid is None:
        log(message="Encerrando programa...",  context=CRITICAL)

    sensor_pool = SensorPool() # todo: totalmente substituivel para programação funcional
    sensor_pool.discover(device_uuid=device_uuid)
    with ThreadPoolExecutor(max_workers=len(sensor_pool.sensors)) as executor:
        executor.map(run, sensor_pool.sensors)


if __name__ == '__main__':
    main()