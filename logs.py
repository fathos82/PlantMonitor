import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from rich.logging import RichHandler

import settings

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)


class ExtraLoggerAdapter(logging.LoggerAdapter):
    def process(self, msg, kwargs):
        kwargs.setdefault("extra", {})
        kwargs["extra"].update(self.extra)
        return msg, kwargs

class CompactContextFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        # contexto visual = raiz (antes do ponto)
        record.context = record.name.split(".")[0]

        # subcontexto opcional
        sub = getattr(record, "sub", None)
        record.subctx = f"[{sub}] " if sub else ""

        return super().format(record)



class ContextLevelFilter(logging.Filter):
    def __init__(self, rules: dict[str, int]):
        super().__init__()
        self.rules = rules

    def filter(self, record: logging.LogRecord) -> bool:
        name = record.name
        level = record.levelno

        # tenta match do mais específico → mais genérico
        parts = name.split(".")

        for i in range(len(parts), 0, -1):
            context = ".".join(parts[:i])
            if context in self.rules:
                return level >= self.rules[context]

        return False



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
        CompactContextFormatter(
            "%(levelname)-8s %(context)-6s | %(subctx)s%(message)s"
        )
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

def get_logger(context: str, **extra):
    base_logger = logging.getLogger(context.upper())

    if extra:
        return ExtraLoggerAdapter(base_logger, extra)

    return base_logger




setup_logging(settings.LOG_RULES)