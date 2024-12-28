from abc import ABC, abstractstaticmethod
from typing import Callable
from google.cloud import pubsub_v1


class TaskQueue(ABC):
    @abstractstaticmethod
    def publish(message: str) -> None:
        raise NotImplementedError

    @abstractstaticmethod
    async def consume(callback: Callable) -> None:
        raise NotImplementedError

class GooglePubSub(TaskQueue):
    @staticmethod
    def publish(message: str) -> None:
        publisher = pubsub_v1.PublisherClient()
        topic_name = 'projects/{project_id}/topics/{topic}'.format(
            project_id=os.getenv('GOOGLE_CLOUD_PROJECT'),
            topic=os.getenv('GOOGLE_CLOUD_TOPIC'),  
        )
        future = publisher.publish(topic_name, bytes(message, 'utf-8'))
        future.result()
    
    @staticmethod
    async def consume(callback) -> None:
        topic_name = 'projects/{project_id}/topics/{topic}'.format(
            project_id=os.getenv('GOOGLE_CLOUD_PROJECT'),
            topic=os.getenv('GOOGLE_CLOUD_TOPIC'),
            )

        subscription_name = 'projects/{project_id}/subscriptions/{sub}'.format(
            project_id=os.getenv('GOOGLE_CLOUD_PROJECT'),
            sub=os.getenv('GOOGLE_CLOUD_SUB'),  
            )

        async with pubsub_v1.SubscriberClient() as subscriber:
            future = subscriber.subscribe(subscription_name, callback)
            await future.result() 


queue_register = {"GCP": GooglePubSub}
