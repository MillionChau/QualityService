import logging
import sys
from app.core.config import settings


def setup_logging() -> logging.Logger:
    logger = logging.getLogger(settings.APP_NAME)
    logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


def setup_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """Trả về logger con với handler riêng, tắt propagate
    để không bị in trùng bởi handler của logger cha/root."""
    log = logging.getLogger(name)
    log.setLevel(level)

    if not log.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)
        log.addHandler(handler)
    log.propagate = False

    return log


logger = setup_logging()
