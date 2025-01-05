from abc import ABC, abstractmethod
from typing import Callable
from google.cloud.pubsub_v1 import PublisherClient
import logging
import os


logging.basicConfig(level=logging.INFO)

class QueuePublisher(ABC):
    """ Abstract base class for queue publishers. """
    @abstractmethod
    def publish(self, message: str) -> None:
        """ Publishes a message to the specified queue. """
        raise NotImplementedError

class GooglePubSubPublisher(QueuePublisher):
    """ Publishes messages to Google Cloud Pub/Sub. """
    def __init__(self, project: str, topic: str):
        # Initialize Google Cloud Pub/Sub client
        self.publisher = PublisherClient()
        self.topic_name = 'projects/{project}/topics/{topic}'.format(
                            project=os.getenv('GOOGLE_CLOUD_PROJECT'), 
                            topic=os.getenv('GOOGLE_CLOUD_TOPIC')
                            )

    def publish(self, message: str) -> None:
        """ Publishes a message to the Google Cloud Pub/Sub topic. """
        # Data must be a bytestring
        message_bytes = message.encode('utf-8')
        future = self.publisher.publish(topic=self.topic_name, data=message_bytes)
        future.result()
        logging.info(f"Published message '{message}' to {self.topic_name}")


