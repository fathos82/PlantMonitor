# sensors/drivers/__init__.py
import importlib
import pkgutil
from pathlib import Path
from logs import get_logger

logger = get_logger("DRIVERS")

_drivers_path = str(Path(__file__).parent)

for _, module_name, _ in pkgutil.iter_modules([_drivers_path]):
    try:
        print(f"sensors.drivers.{module_name}")
        importlib.import_module(f"sensors.drivers.{module_name}")
        logger.debug("Driver carregado: %s", module_name)
    except Exception as e:
        logger.error("Falha ao carregar driver: %s — %s", module_name, e)

