import logging
import os

SENSOR_SLEEP_TIME = float(os.getenv("SENSOR_SLEEP_TIME", 0.2))
WATCHER_SLEEP_TIME = int(os.getenv("WATCHER_SLEEP_TIME", 5))
SENSOR_ERROR_SLEEP_TIME = int(os.getenv("SENSOR_ERROR_SLEEP_TIME", 1))
BASE_URL = os.getenv("BASE_URL", "http://192.168.0.107:8080/")
MQTT_ADDRESS = os.getenv("MQTT_ADDRESS", "192.168.0.107")

BASE_API_URL = BASE_URL + "api/"
SENSOR_API_URL = BASE_API_URL + "sensors/"
DEVICE_API_URL = BASE_API_URL + "devices/"



LOG_RULES = {
    "SYSTEM": logging.DEBUG,
    "SENSOR_POOL": logging.DEBUG,
    "SENSOR_WORKER": logging.DEBUG,
    "DEVICE": logging.DEBUG,
    "CAMERA": logging.DEBUG,
}