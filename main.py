import time
from concurrent.futures import ThreadPoolExecutor

from sensors.sensor_manager import SensorPool
from sensors.sensor_utils import load_sensors
from sensors.sensors import AbstractSensor
from utils import register_device, generate_qrcode_to_set_account, send_data


def run(sensor: AbstractSensor):
    while True:
        value = sensor.read()
        print(
            f"\n──────── Sensor ────────\n"
            f"Type  : {sensor.__class__.__name__}\n"
            f"Value : {value}\n"
            f"────────────────────────"
        )
        send_data(value)
        time.sleep(0.01)





def main():
    # todo: improve logs
    # todo: verify is exists qr code
    device_id = register_device()
    # generate from token, not uuid.
    # generate_qrcode_to_set_account(device_id)
    sensor_pool = SensorPool() # todo: totalmente substituivel para programação funcional
    sensor_pool.discover()
    with ThreadPoolExecutor(max_workers=len(sensor_pool.sensors)) as executor:
        executor.map(run, sensor_pool.sensors)


if __name__ == '__main__':
    main()