import logging

logger = logging.getLogger("coro_runner")

def update_logger(log_level: int) -> None:
    logger.setLevel(log_level)
    logger.addHandler(logging.StreamHandler())
