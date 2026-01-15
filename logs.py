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


def setup_logging(rules: dict[str, int], default_level=logging.DEBUG):
    # Formatter para arquivo (completo)
    file_formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Rich handler (console)
    rich_handler = RichHandler(
        show_time=False,
        show_level=True,
        show_path=False,
        rich_tracebacks=True,
        log_time_format=None
    )

    # 👉 Formatter do Rich: CONTEXTO + mensagem
    rich_handler.setFormatter(
        logging.Formatter("%(name)s | %(message)s")
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

    root_logger = logging.getLogger()
    root_logger.setLevel(default_level)
    root_logger.handlers.clear()

    root_logger.addHandler(rich_handler)
    root_logger.addHandler(file_handler)

def get_logger(context: str):
    """
    Retorna um logger com o contexto como nome
    Ex: MQTT, SENSOR, API
    """
    return logging.getLogger(context.upper())



setup_logging(settings.LOG_RULES)