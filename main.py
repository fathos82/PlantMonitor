# todo: problema com GPIO -> https://chatgpt.com/c/695d3a4d-83a0-8332-9ff5-78f43c82bce9
# Alternativa: sudo apt install python3.13-dev
# sudo apt update
# sudo apt install -y ffmpeg

import threading
import time
from logging import CRITICAL

import mqtt_client
from cams.stream_publisher import StreamPublisher
from sensors.sensor_pool import sensor_pool
from settings import  WATCHER_SLEEP_TIME
from thread_supervisor import thread_supervisor
from utils import register_or_get_device, generate_qrcode_to_set_account



def device_watcher(device_uuid):
    # todo: criar variável de controlle
    # todo: verificar se precisa de logos
    while True:
        sensor_pool.discover(device_uuid)
        for sensor_id in sensor_pool.sensors_to_remove:
            thread_supervisor.remove_sensor(sensor_id)
        for sensor_id in sensor_pool.sensors_to_add:
            thread_supervisor.add_sensor(sensor_pool.sensors_map[sensor_id])
        for sensor_id in sensor_pool.sensors_to_update:
            thread_supervisor.reload_sensor(sensor_id)
        sensor_pool.clear()
        time.sleep(WATCHER_SLEEP_TIME)



def main():
    # todo: improve logs
    # todo: verify is exists qr code

    publisher = StreamPublisher(
        source="rtsp://quarto:quarto123@192.168.0.120:554/stream1",
        destination_rtmp="rtmp://161.97.148.7:1935/any",
        source_type="ip",
        reencode=False,
    )

    publisher.start()


    device_uuid = register_or_get_device()
    mqtt_client.connect()
    device_thread = threading.Thread(target=device_watcher, args=(device_uuid,))
    device_thread.start()




if __name__ == '__main__':
    main()