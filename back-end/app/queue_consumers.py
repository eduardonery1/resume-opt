import logging
import os
import asyncio
from abc import ABC, abstractmethod
from google.cloud import pubsub_v1
from typing import Callable
from asyncio.futures import Future


class QueueConsumer(ABC):
    @abstractmethod
    def consume(self, callback: Callable) -> None:
       raise NotImplementedError


class GooglePubSubConsumer(QueueConsumer):
    def __init__(self, project: str, sub: str):
        self._subscription_name = 'projects/{project_id}/subscriptions/{sub}'.format(
            project_id=project,
            sub=sub,  
            )

        self._consumer = pubsub_v1.SubscriberClient()

    async def consume(self, callback: Callable) -> None:
        try:
            future = self._consumer.subscribe(self._subscription_name, callback)
            await asyncio.wrap_future(future)
        except IOError as e:
            logging.exception("Failed subcribing to Google PubSub.")
            raise e

            

