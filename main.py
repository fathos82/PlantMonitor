import threading
import time
import sensors.drivers

from api import mqtt, client

# TODO: FIX ERROR CREATING SENSOR BY STRING/ENUM
from api.mqtt import mqtt_client
from device import identity as device_identity
from device_info import DeviceInfo
from publisher import Publisher
from sensors.pool import sensor_pool
from settings import WATCHER_SLEEP_TIME, BASE_API_URL




def device_watcher(device_infor:DeviceInfo):
    while True:
        try:
            client.ping_device(device_infor.device_id)
            sensor_pool.discover(device_infor.device_uuid)
        except Exception:
            pass  # log tratado dentro do pool
        time.sleep(WATCHER_SLEEP_TIME)


def main():
    device_info:DeviceInfo = device_identity.load_or_create()
    mqtt_client.connect(device_info.device_uuid)
    publisher = Publisher(mqtt_client, device_info.device_uuid)
    publisher.add_filter(KalmanFilter1D())
    sensor_pool.set_publisher(publisher)

    device_thread = threading.Thread(
        target=device_watcher,
        args=(device_info,),
        daemon=True,
    )
    device_thread.start()
    device_thread.join()


if __name__ == '__main__':
    main()