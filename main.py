# todo: problema com GPIO -> https://chatgpt.com/c/695d3a4d-83a0-8332-9ff5-78f43c82bce9
# Alternativa: sudo apt install python3.13-dev
import random
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from logging import CRITICAL

from sensors.sensor_manager import SensorPool
from sensors.sensors import AbstractSensor
from settings import log
from utils import register_or_get_device, generate_qrcode_to_set_account, send_data
SLEEP_TIME = 0.5
def run(sensor: AbstractSensor, stop_event: threading.Event):
    while not stop_event.is_set():
        try:
            value = sensor.read()
            dt = datetime.now(timezone.utc)
            timestamp = dt.isoformat().replace("+00:00", "Z")
            send_data(value, sensor, timestamp)
            time.sleep(SLEEP_TIME)
        except Exception as e:
            # todo: verificar integridade, caso não integro reportar ao backend.
            pass

def run_device_thread(stop_event: threading.Event):
    while True:

        random_float= random.random()
        if random_float < 0.01:
            stop_event.set()
            print("PARANDO...")
        time.sleep(0.5)



def main():
    # todo: improve logs
    # todo: verify is exists qr code
    device_uuid = register_or_get_device()
    if device_uuid is None:
        log(message="Encerrando programa...",  context=CRITICAL)
    sensor_pool = SensorPool() # todo: totalmente substituivel para programação funcional
    sensor_pool.discover(device_uuid=device_uuid)
    stop_event = threading.Event()
    device_thread = threading.Thread(target=run_device_thread, args=(stop_event,))
    device_thread.start()
    while True:
        with ThreadPoolExecutor(max_workers=len(sensor_pool.sensors)) as executor:
            for sensor in sensor_pool.sensors:
                executor.submit(run, sensor, stop_event)
        stop_event.clear()


if __name__ == '__main__':
    main()