from abc import ABC, abstractmethod
from typing import Callable
from google.cloud.pubsub_v1 import PublisherClient
import logging


logging.basicConfig(level=logging.INFO)

class QueuePublisher(ABC):
    def __init__(self, channel: str):
        self.channel = channel

    @abstractmethod
    def publish(self, message: str) -> None:
        raise NotImplementedError

class GooglePubSubPublisher(QueuePublisher):
    def __init__(self, channel: str, project: str):
        super().__init__(channel)
        self.project = project
        # Initialize Google Cloud Pub/Sub client
        self.publisher = PublisherClient()
        self.topic_name = 'projects/{project}/topics/{topic}'.format(
                            project=self.project, 
                            topic=self.channel
                            )

    def publish(self, message: str) -> None:
        # Data must be a bytestring
        message_bytes = message.encode('utf-8')
        future = self.publisher.publish(topic=self.topic_name, data=message_bytes)
        future.result()
        logging.info(f"Published message '{message}' to {self.topic_name}")


