import threading
import time

from api import mqtt
from device import identity as device_identity
from sensors.pool import sensor_pool
from settings import WATCHER_SLEEP_TIME


def device_watcher(device_uuid: str):
    while True:
        try:
            sensor_pool.discover(device_uuid)
        except Exception:
            pass  # log tratado dentro do pool
        time.sleep(WATCHER_SLEEP_TIME)


def main():
    # device_uuid = device_identity.load_or_create()
    mqtt.connect()

    device_thread = threading.Thread(
        target=device_watcher,
        args=(None,),
        daemon=True,
    )
    device_thread.start()
    device_thread.join()


if __name__ == '__main__':
    main()