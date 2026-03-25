# sensors/drivers/__init__.py
import importlib
import pkgutil
from pathlib import Path
from logs import get_logger

from sensors.drivers import lm35dzt
logger = get_logger("DRIVERS")

_drivers_path = str(Path(__file__).parent)

for _, module_name, _ in pkgutil.iter_modules([_drivers_path]):
    try:
        importlib.import_module(f"sensors.drivers.{module_name}")
        logger.debug("Driver carregado: %s", module_name)
    except Exception:
        logger.exception("Falha ao carregar driver: %s — ignorado", module_name)