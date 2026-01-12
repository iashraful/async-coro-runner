import asyncio
import logging
from random import random

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())



async def rand_delay(msg: str, unit: int = 5):
    await asyncio.sleep(random() * unit)
    return f"Done - rand_delay - {msg}"


async def dummy_email_send(recipient_emails: list[str]):
    logger.info("emails: %s", recipient_emails)
    await asyncio.sleep(random() * 3)
    return "Done - dummy_email_send"
