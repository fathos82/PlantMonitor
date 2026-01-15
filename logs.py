import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from rich.logging import RichHandler

import settings

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)


class ContextLevelFilter(logging.Filter):
    def __init__(self, rules: dict[str, int]):
        super().__init__()
        self.rules = rules

    def filter(self, record: logging.LogRecord) -> bool:
        context = record.name
        level = record.levelno

        if context not in self.rules:
            return False

        return level >= self.rules[context]




def setup_logging(
    rules: dict[str, int],
    default_level=logging.DEBUG
):
    file_formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    rich_handler = RichHandler(
        show_time=False,
        show_level=True,
        show_path=False,
        rich_tracebacks=True
    )

    file_handler = RotatingFileHandler(
        LOG_DIR / "app.log",
        maxBytes=5_000_000,
        backupCount=5
    )
    file_handler.setFormatter(file_formatter)

    context_filter = ContextLevelFilter(rules)
    rich_handler.addFilter(context_filter)
    file_handler.addFilter(context_filter)

    logging.basicConfig(
        level=default_level,
        handlers=[rich_handler, file_handler]
    )

import logging

def get_logger(context: str):
    """
    Retorna um logger com o contexto como nome
    Ex: MQTT, SENSOR, API
    """
    return logging.getLogger(context.upper())



setup_logging(settings.LOG_RULES)