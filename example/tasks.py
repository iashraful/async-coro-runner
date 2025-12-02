import asyncio
import logging
from random import random

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())



async def rand_delay(msg: str, unit: int = 5):
    current_task: asyncio.Task | None = asyncio.current_task()
    logger.info(
        f"{msg} | Random Delay started: {current_task.get_name() if current_task else 'No Name'}",
    )
    await asyncio.sleep(random() * unit)
    logger.info(
        f"Random Delay ended: {current_task.get_name() if current_task else 'No name'}"
    )
    return f"Done - {current_task.get_name() if current_task else 'No name'}"


async def dummy_email_send(recipient_emails: list[str]):
    current_task: asyncio.Task | None = asyncio.current_task()
    logger.info("emails: %s", recipient_emails)
    logger.info(
        f"Dummy Send Email started: {current_task.get_name() if current_task else 'No Name'}",
    )
    await asyncio.sleep(random() * 3)
    logger.info(
        f"Dummy Send Email ended: {current_task.get_name() if current_task else 'No name'}"
    )
