import os
from dotenv import load_dotenv
import json
import asyncio
from aio_pika import connect, IncomingMessage
import json

load_dotenv()

user = os.environ["RABBITMQ_USER"]
password  = os.environ["RABBITMQ_PASS"]
host = os.environ["RABBITMQ_HOST"]
port = os.environ["RABBITMQ_PORT"]

queue_name= "task-queue"

url = f'amqp://{user}:{password}@{host}:{port}/%2F'


async def callback(message: IncomingMessage):
    print('recieved a massage in api gateaway')
    txt = message.body.decode("utf-8")
    data = json.loads(txt)
    print(data)

async def main(loop):
    connection = await connect(url, loop = loop)
    channel = await connection.channel()
    queue = await channel.declare_queue(queue_name)
    await queue.consume(callback, no_ack = True)
    print("start consuming ")


if __name__=="__main__":
    loop = asyncio.get_event_loop()
    loop.create_task(main(loop))
    loop.run_forever()
