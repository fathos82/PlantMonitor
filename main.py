# todo: problema com GPIO -> https://chatgpt.com/c/695d3a4d-83a0-8332-9ff5-78f43c82bce9
# Alternativa: sudo apt install python3.13-dev
import threading
import time
from logging import CRITICAL

from sensors.sensor_pool import SensorPool, sensor_pool
from settings import log, WATCHER_SLEEP_TIME
from thread_supervisor import thread_supervisor
from utils import register_or_get_device, generate_qrcode_to_set_account, send_data



def device_watcher(device_uuid):
    # todo: criar variável de controlle
    while True:
        sensor_pool.discover(device_uuid)
        print("PARA ATUALIZAR: ", sensor_pool.sensor_to_update)
        for sensor in sensor_pool.sensors_to_remove:
            thread_supervisor.remove_sensor(sensor)
        for sensor in sensor_pool.sensors_to_add:
            thread_supervisor.add_sensor(sensor)
        for sensor in sensor_pool.sensor_to_update:
            print("ATUALIZANDO SENSOR: ", sensor)
            thread_supervisor.reload_sensor(sensor)
        sensor_pool.clear()
        time.sleep(WATCHER_SLEEP_TIME)



def main():
    # todo: improve logs
    # todo: verify is exists qr code
    device_uuid = register_or_get_device()
    if device_uuid is None:
        log(message="Encerrando programa...",  context=CRITICAL)
    device_thread = threading.Thread(target=device_watcher, args=(device_uuid,))
    device_thread.start()




if __name__ == '__main__':
    main()