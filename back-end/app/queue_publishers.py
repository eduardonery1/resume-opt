from abc import ABC, abstractmethod
from typing import Callable, Optional
from google.cloud.pubsub_v1 import PublisherClient
import logging
import asyncio
import os



class QueuePublisher(ABC):
    """ Abstract base class for queue publishers. """
    @abstractmethod
    def publish(self, message: str) -> None:
        """ Publishes a message to the specified queue. """
        raise NotImplementedError

class GooglePubSubPublisher(QueuePublisher):
    """ Publishes messages to Google Cloud Pub/Sub. """
    def __init__(self, project: Optional[str] = None):
        self._project = project or os.getenv('GOOGLE_CLOUD_PROJECT')
        if not self._project:
            raise ValueError("Project must be specified.")

    async def publish(self, message: str, topic: Optional[str] = None) -> None:
        """ Publishes a message to the Google Cloud Pub/Sub topic. """
        if not topic:
            raise ValueError("Topic must be specified.")

        topic_name = 'projects/{project}/topics/{topic}'.format(
                            project=self._project, 
                            topic=topic
                            )
        # Data must be a bytestring
        message_bytes = message.encode('utf-8')
        future = self.publisher.publish(topic=topic_name, data=message_bytes)
        await asyncio.wrap_future(future)
        logging.info(f"Published message '{message}' to {topic_name}")


