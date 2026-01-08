import logging
import logging
import sys
from enum import Enum



SENSOR_SLEEP_TIME = 0.2
WATCHER_SLEEP_TIME = 5
SENSOR_ERROR_SLEEP_TIME = 1



class LogLevel(Enum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class LogContext(Enum):
    SYSTEM = "SYSTEM"
    DEVICE = "DEVICE"
    API = "API"
    MQTT = "MQTT"
    SENSOR = "SENSOR"



logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%d/%m/%Y %H:%M:%S"
)

_logger = logging.getLogger("plantmonitor")


def log(message, level=LogLevel.INFO, context=None):
    """
    Log padronizado para o projeto PlantMonitor
    """

    # Normaliza nível
    if isinstance(level, LogLevel):
        level_value = level.value
    else:
        level_value = str(level).lower()

    # Normaliza contexto
    if isinstance(context, LogContext):
        context_value = context.value
    else:
        context_value = context

    prefix = f"[{context_value}] " if context_value else ""

    if level_value == "debug":
        _logger.debug(prefix + message)
    elif level_value == "warning":
        _logger.warning(prefix + message)
    elif level_value == "error":
        _logger.error(prefix + message)
    elif level_value == "critical":
        _logger.critical(prefix + message)
        sys.exit(1)
    else:
        _logger.info(prefix + message)
