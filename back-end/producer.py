import asyncio
import logging

import aio_pika

async def connect() -> None:
    connection = await aio_pika.connect_robust(
        "amqp://guest:guest@127.0.0.1/",
    )
    return connection

async def publisher(message: str, route_key: str) -> None:
    logging.basicConfig(level=logging.DEBUG)
    conn = await connect()

    async with conn:
        ch = await conn.channel()
        await ch.default_exchange.publish(
            aio_pika.Message(body=message.encode()),
            routing_key=routing_key,
        )
