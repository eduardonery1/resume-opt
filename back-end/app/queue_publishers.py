from abc import ABC, abstractmethod
from typing import Callable


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
        from google.cloud import pubsub_v1
        self.publisher = pubsub_v1.PublisherClient()
        self.topic_name = 'projects/{project}/topics/{topic}'.format(
                            project=self.project, 
                            topic=self.channel
                            )

    def publish(self, message: str) -> None:
        # Data must be a bytestring
        message_bytes = message.encode('utf-8')
        future = self.publisher.publish(self.topic_name, data=message_bytes)
        future.result()


