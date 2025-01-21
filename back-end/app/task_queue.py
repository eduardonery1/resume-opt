from abc import ABC, abstractmethod
from typing import Callable, Dict, Tuple, Set
from google.cloud.pubsub_v1 import PublisherClient, SubscriberClient
from google.cloud.pubsub_v1.subscriber.message import Message
from tasks import TaskRequest, TaskResponse, TaskManager
from dotenv import load_dotenv
from utils import exp_backoff, exp_sleep
from exceptions import UnableToPublishTask
from storages import TaskResponseStorage
from asyncio import AbstractEventLoop
from dependency_injector import containers, providers
from dependency_injector.wiring import Provide, inject
import functools
import threading
import os
import asyncio
import logging

load_dotenv()


class TaskQueue(ABC):
    @abstractmethod
    def consume(*args, **kwargs):
        raise NotImplementedError

    @abstractmethod
    def publish(message: str, *args, **kwargs):
        raise NotImplementedError


class TaskQueuePublisher(ABC):
    def __init__(self, queue: TaskQueue):
        self._queue = queue

    @abstractmethod
    def publish_task(
        message: str, 
        storage: TaskResponseStorage, 
        *args, **kwargs
    ):
        raise NotImplementedError


class GooglePubSubTopicManager:
    """ Manages Google Pub/Sub topics and subscriptions for tasks. """
    def __init__(self) -> None:
        self.task_name_to_topic_sub_pair: Dict[str, Tuple[str, str]] = {
                "test-task": ("test-topic", "test-sub")
        } # Prototype for development

    def get_topic_sub_pair(self, task_name: str) -> Tuple[str, str]:
        """Retrieves the topic and subscription pair for a given task name."""
        pair = self.task_name_to_topic_sub_pair.get(task_name)
        if not pair:
            raise InvalidTaskName(f"Task name '{task_name}' not found.")
        return pair


class GooglePubSubRequestCallback:
    """ Handles callbacks from Google Pub/Sub subscriptions. """
    def __init__(
            self, 
            loop: AbstractEventLoop, 
            task_manager: TaskManager
        ) -> None:

        self._id_to_storage_lock = asyncio.Lock()
        self._id_to_storage = {}

        self._futures_lock = threading.Lock()
        self._futures = {}
        
        self._task_manager = task_manager
        if not loop:
            self._loop = asyncio.get_running_loop()

    async def set_storage_to_id(
            self, 
            storage: TaskResponseStorage, 
            request_id: str
        ) -> None:

        if not isinstance(request_id, str):
            raise TypeError("Parameter 'id' must be of type str.")

        if not isinstance(storage, TaskResponseStorage):
            raise TypeError(
                "Parameter 'storage' must be derived from 'TaskResponseStorage'."
            )

        async with self._id_to_storage_lock:
            self._id_to_storage[request_id] = storage
        logging.info(f"Successfully associated storage with ID: {request_id}.")

    async def _execute_task(
        self, 
        request_id: str, 
        request: TaskRequest, 
        message: Message
    ) -> None:
        logging.debug(
            f"GooglePubSub._update_storage: \
                id = {request_id}, \
                result = {request}, \
                message: {message}."
        )
        if not self._loop.is_running():
            message.nack()
            raise RuntimeError("Event loop is closed.")

        async with self._id_to_storage_lock:
            storage = self._id_to_storage.get(request_id)

        if storage is None:
            logging.warning(f"No storage found for ID: {request_id}.")
            message.ack() # Try again later
            return
        
        logging.info(f"Processing request {request_id}...")
        result = self._task_manager.process_task(request) 
        logging.info(f"Task {request_id} result: {result.model_dump_json()}.")
        
        try:
            logging.info(f"Updating storage for ID: {request_id}.")
            await storage.update(request_id, result.model_dump_json())
        except RedundantResponseError:
            logging.exception(f"Redundant response received for ID: {request_id}.")
            message.ack()
        except Exception as e:
            logging.exception(f"{self.__class__.__name__}._update_storage: Error updating storage for ID: {request_id}: {e}")
            message.ack()
        else:
            message.ack()
            logging.info(f"Message with ID: {result.id} was sent to storage.")

    def _cleanup_future(self, message, request_id: str):
        with self._futures_lock:
            self._futures.pop(request_id)

    def __call__(self, message: Message) -> None:
        logging.info(f"Callback received message: {message.data}.")

        try:
            request = TaskRequest.model_validate_json(message.data) 
        except ValidationError:
            logging.exception(f"Invalid TaskRequest format: {message.data}")
            message.ack() 
            return

        future = asyncio.run_coroutine_threadsafe(
            self._execute_task(request.id, request, message), 
            loop=self._loop
        )

        with self._futures_lock:
            self._futures[request.id] = future

        future.add_done_callback(
            functools.partial(self._cleanup_future, request_id = request.id)
        )


class GooglePubSub(TaskQueue):
    def __init__(self, project: str = None):
        self._project = project
        if not self._project:
            raise ValueError("Project ID must be provided.")

        self._pub_client = PublisherClient()
        self._consumer_client = SubscriberClient()

        self._lock_pub_pool = threading.Lock()
        self._pub_pool = {}

        self._lock_consumer_pool = threading.Lock()
        self._consumer_pool = {} # One consumer per subscription.  There is a low fixed amount of consumers.

    def _cleanup_pub_future(self, message, key, topic):
        with self._lock_pub_pool:
            future = self._pub_pool.get(key) # This will always return a future 

        try:
            message_id = future.result()

        except Exception as e:
            logging.exception(
                f"Error processing future for key {key}: {e}. Resuming publish..."
            )
            self._pub_client.resume_publish(topic, message_id)
        else:
            logging.info(
                f"Future for message ID: '{message_id}' was successfully published."
            )

    def _cleanup_sub_future(self, message, key):
        with self._lock_consumer_pool:
            self._consumer_pool.pop(key)
        logging.info(f"Subscription '{key}' was successfully cancelled.")
 
    def publish(self, message: str, topic: str, request_id: str, tries = 3) -> None:
        topic_name = 'projects/{project}/topics/{topic}'.format(
            project=self._project,
            topic=topic,  
        )
        
        future = self._pub_client.publish(topic_name, message.encode('utf-8')) # This has internal retries and timeout
        logging.info(f"Message with ID: {request_id} was sent to topic: '{topic}'.")

        with self._lock_pub_pool:
            self._pub_pool[request_id] = future

        future.add_done_callback(
                functools.partial(self._cleanup_pub_future, key = request_id, topic = topic))

    def consume(self, subscription: str, callback: Callable) -> None:
        with self._lock_consumer_pool: 
            if subscription in self._consumer_pool: # One kind of task has a specific consumer running, there is a low fixed amount of consumers.
                logging.info(
                    f"This subscription {subscription} is already being listened to."
                ) 
                return 

        logging.info(f"Consuming from '{subscription}'...")
        subscription_name = 'projects/{project}/subscriptions/{sub}'.format(
            project=self._project,
            sub=subscription
        )

        future = self._consumer_client.subscribe(subscription_name, callback) # This runs on a separate thread

        with self._lock_consumer_pool:
            self._consumer_pool[subscription] = future

        future.add_done_callback(
            functools.partial(self._cleanup_sub_future, key = subscription)
        ) # As the callback removes the future from _consumer_pool, guarantee it's there first.

        logging.info(f"Listening to messages of subscription: '{subscription}'.")


class Container(containers.DeclarativeContainer):
    queue = providers.ThreadSafeSingleton(
        GooglePubSub, 
        project=os.getenv("GOOGLE_CLOUD_PROJECT")
    )
    callback = providers.ThreadSafeSingleton(
        GooglePubSubRequestCallback, 
        loop=None,
        task_manager=TaskManager()
    )
    topic_manager = providers.ThreadSafeSingleton(
        GooglePubSubTopicManager
    )

@inject
class GooglePubSubTaskPublisher(TaskQueuePublisher):
    """ Class responsible for requesting tasks using Google Pub/Sub as a message queue. """
    def __init__(
        self, 
        queue: GooglePubSub = Provide[Container.queue], 
        topic_manager: GooglePubSubTopicManager = Provide[Container.topic_manager], 
        callback: GooglePubSubRequestCallback = Provide[Container.callback],
    ) -> None:
        
        if not (queue or topic_manager or callback):
            raise ValueError(
                "All arguments must be provided correctly."
            )

        super().__init__(queue) 
        self._topic_manager = topic_manager
        self._callback = callback

    async def publish_task(
        self, 
        message: TaskRequest,
        storage: TaskResponseStorage
    ) -> None:
        """ 
        Publishes a task to Google Pub/Sub.
        Args:
            message: The task message.
            storage: The storage to use for task responses.
            tries: The number of retries to attempt if publishing fails.
        Raises:
            ValueError: If the message or storage is invalid.
            UnableToPublishTask: If publishing fails after multiple retries.
        """

        if not isinstance(message, TaskRequest):
            raise ValueError(
                "'message' argument must be derived from TaskRequest."
            )

        if not isinstance(storage, TaskResponseStorage):
            raise ValueError(
                "'storage' argument must be derived from TaskResponseStorage."
            )

        try:
            topic, sub = self._topic_manager.get_topic_sub_pair(
                message.task_name
            )

        except InvalidTaskName:
            logging.critical(
                "Invalid task name sent to queue.\
                Possible causes are: incorrect endpoint configuration,\
                environment error or TopicManager issue."
            )
            raise

        logging.info(
            f"Publishing task '{message.task_name}' with ID '{message.id}' to topic '{topic}'."
        )
        await self._callback.set_storage_to_id(storage, message.id)

        self._queue.publish(message.model_dump_json(), topic, message.id)
        self._queue.consume(sub, self._callback)


cont = Container()
cont.wire(modules=[__name__])

