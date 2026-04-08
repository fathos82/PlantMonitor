import logging
import os

from dotenv import load_dotenv

load_dotenv()

# TODO: TORNAR ISSO CONFIGURAVEL PELO USUARIO A NIVEL DE API
SENSOR_SLEEP_TIME = float(os.getenv("SENSOR_SLEEP_TIME", 0.5))
WATCHER_SLEEP_TIME = int(os.getenv("WATCHER_SLEEP_TIME", 5))
SENSOR_ERROR_SLEEP_TIME = int(os.getenv("SENSOR_ERROR_SLEEP_TIME", 1))
BASE_URL = os.getenv("BASE_URL", "http://192.168.0.107:8080/")
MQTT_ADDRESS = os.getenv("MQTT_ADDRESS", "192.168.0.107")

BASE_API_URL = BASE_URL + "/api/"
BASE_API_URL = BASE_API_URL.replace("//api", "/api")
SENSOR_API_URL = BASE_API_URL + "sensors/from_device/"
DEVICE_API_URL = BASE_API_URL + "devices/"
SENSOR_ERROR_API_URL = SENSOR_API_URL +"{id}/errors/"
PUBLISHER_BATCH_SIZE = int(os.getenv("PUBLISHER_BATCH_SIZE", 10))
PUBLISHER_BATCH_INTERVAL = float(os.getenv("PUBLISHER_BATCH_INTERVAL", 5.0))  # segundos

import logging
import os
from dotenv import load_dotenv

load_dotenv()

# Configurações existentes
SENSOR_SLEEP_TIME = float(os.getenv("SENSOR_SLEEP_TIME", 0.5))
WATCHER_SLEEP_TIME = int(os.getenv("WATCHER_SLEEP_TIME", 5))
SENSOR_ERROR_SLEEP_TIME = int(os.getenv("SENSOR_ERROR_SLEEP_TIME", 1))
BASE_URL = os.getenv("BASE_URL", "http://192.168.0.107:8080/")
MQTT_ADDRESS = os.getenv("MQTT_ADDRESS", "192.168.0.107")


# Configuração de logs (corrigida)
# ===============================
DEFAULT_LOG_RULES = {
    "SYSTEM": logging.DEBUG,
    "SENSOR_POOL": logging.INFO,
    "SENSOR_WORKER": logging.INFO,
    "DEVICE": logging.INFO,
    "CAMERA": logging.INFO,
    "API_CLIENT": logging.INFO,
    "MQTT": logging.INFO,
    "PUBLISHER": logging.INFO,
}

def parse_log_level(level_str):
    return getattr(logging, level_str.upper(), logging.DEBUG)

# Checa se existe LOG_LEVEL_GLOBAL
global_level_str = os.getenv("LOG_LEVEL_GLOBAL")
if global_level_str:
    global_level = parse_log_level(global_level_str)
    LOG_RULES = {key: global_level for key in DEFAULT_LOG_RULES}
else:
    LOG_RULES = {}
    for key, default in DEFAULT_LOG_RULES.items():
        env_var = f"LOG_LEVEL_{key}"
        level_str = os.getenv(env_var)
        if level_str:
            LOG_RULES[key] = parse_log_level(level_str)
        else:
            LOG_RULES[key] = default

# Aplica os níveis aos loggers
for key, level in LOG_RULES.items():
    logger = logging.getLogger(key)
    logger.setLevel(level)