import threading
import time

import mqtt_client
from device import identity as device_identity
from sensors.pool import sensor_pool
from settings import WATCHER_SLEEP_TIME
from thread_supervisor import thread_supervisor


def device_watcher(device_uuid: str):
    while True:
        try:
            sensor_pool.discover(device_uuid)
            for sensor_id in sensor_pool.sensors_to_remove:
                thread_supervisor.remove_sensor(sensor_id)
            for sensor_id in sensor_pool.sensors_to_add:
                thread_supervisor.add_sensor(sensor_pool.sensors_map[sensor_id])
            for sensor_id in sensor_pool.sensors_to_update:
                thread_supervisor.reload_sensor(sensor_id)
            sensor_pool.clear()
        except Exception:
            pass  # log tratado dentro do pool
        time.sleep(WATCHER_SLEEP_TIME)


def main():
    device_uuid = device_identity.load_or_create()
    mqtt_client.connect()

    device_thread = threading.Thread(
        target=device_watcher,
        args=(device_uuid,),
        daemon=True,
    )
    device_thread.start()
    device_thread.join()


if __name__ == '__main__':
    main()