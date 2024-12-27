import asyncio
import logging
import aio_pika


logging.basicConfig(level=logging.DEBUG)

async def connect() -> None:
    connection = await aio_pika.connect_robust(
        "amqp://guest:guest@localhost/",
    )
    return connection

async def publish(message: str, route_key: str) -> None:
    conn = await connect()

    async with conn:
        ch = await conn.channel()
        await ch.default_exchange.publish(
            aio_pika.Message(body=message.encode()),
            routing_key=routing_key,
        )
