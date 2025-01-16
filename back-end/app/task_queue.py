from abc import ABC, abstractmethod
from typing import Callable, Dict, Tuple
from google.cloud.pubsub_v1 import PublisherClient, SubscriberClient
from google.cloud.pubsub_v1.subscriber.message import Message
from tasks import TaskRequest, TaskResponse
from dotenv import load_dotenv
from utils import exp_backoff, exp_sleep
from exceptions import UnableToPublishTask
from storages import TaskResponseStorage
from asyncio import AbstractEventLoop
from functools import partial
from dependency_injector import containers, providers
from dependency_injector.wiring import Provide, inject
import threading
import os
import asyncio
import logging

load_dotenv()


class TaskQueue(ABC):
    @abstractmethod
    async def publish_task(message: TaskRequest, storage: TaskResponseStorage) -> None:
        raise NotImplementedError

class TaskQueueCleaner(ABC):
    @abstractmethod
    async def clean_queue(queue: TaskQueue) -> None:
        raise NotImplementedError

class TaskQueueFactory:
    @staticmethod
    def create() -> TaskQueue:
        return GooglePubSub(os.getenv('GOOGLE_CLOUD_PROJECT')) 

class GooglePubSubCleaner(TaskQueueCleaner):
    @staticmethod
    async def clean_queue() -> None:
        # This is a placeholder implementation.  A real implementation would need to
        # interact with Google Pub/Sub to delete messages from a topic or subscription.
        logging.warning("GooglePubSubCleaner.clean_queue is not implemented.")
        pass

class GooglePubSubTopicManager:
    """ Manages Google Pub/Sub topics and subscriptions for tasks. """
    task_name_to_topic_sub_pairs = {"test-task": ("test-topic", "test-sub")} # Prototype for development
    
    @staticmethod
    def get_topic_sub_pair(task_name: str) -> Tuple:
        try:
            return GooglePubSubTopicManager.task_name_to_topic_sub_pairs[task_name]
        except KeyError:
            raise InvalidTaskName(f"Task name '{task_name}' not found.")


class GooglePubSubCallback:
    """ Handles callbacks from Google Pub/Sub subscriptions. """
    
    def __init__(self, loop: AbstractEventLoop) -> None:
        self._id_to_storage_lock = asyncio.Lock()
        self._id_to_storage = {}

        self._futures_lock = threading.Lock()
        self._futures = {}

        self._loop = loop

    async def set_storage_to_id(self, storage: TaskResponseStorage, id: str) -> None:
        """Sets the storage associated with a given ID.

        Args:
            id: The ID to associate with the storage.
            storage: The storage to associate with the ID.
        """
        if not isinstance(id, str):
            raise TypeError("Parameter 'id' must be of type str.")

        if not isinstance(storage, TaskResponseStorage):
            raise TypeError("Parameter 'storage' must be derived from 'TaskResponseStorage'.")

        async with self._id_to_storage_lock:
            self._id_to_storage.update({id: storage})
        logging.info(f"Successfully associated storage with ID: {id}.")

    async def _update_storage(self, id: str, result: TaskResponse, message: Message):
        logging.debug(f"GooglePubSub._update_storage: id = {id}, result = {result}, message: {message}.")

        async with self._id_to_storage_lock:
            storage = self._id_to_storage.get(id, None)

        if storage is None:
            logging.warning(f"No storage found for ID: {id}.")
            message.nack() # Try again later
            return
        
        try:
            await exp_backoff(storage.update(id, result.model_dump_json()))

        except RedundantResponseError:
            logging.exception(f"Redundant response received for ID: {id}.")
            message.ack()

        except Exception as e:
            logging.exception(f"GooglePubSubCallback._update_storage: Error updating storage for ID: {id}: {e}")
            message.nack()
        
        else:
            message.ack()
            logging.info(f"Message with ID: {result.id} was sent to storage.")

    def _cleanup_future(self, message, id: str):
        with self._futures_lock:
            self._futures.pop(id)

    def __call__(self, message: Message) -> None:
        """ This callback receives messages from a Google Pub/Sub subscription, 
        validates the message format, updates the corresponding storage with the result, 
        and acknowledges or negatively acknowledges the message based on success or failure.
        """
        logging.info(f"Callback received message: {message.data}.")

        if not self._loop.is_running(): 
            message.nack()
            logging.warning("Event loop is not running.")
            return 

        try:
            result = TaskResponse.model_validate_json(message.data) 
            
        except ValidationError:
            logging.exception(f"Invalid TaskResponse format: {message.data}")
            message.ack() # Don't polute topic with bad formated messages.
            return

        future = asyncio.run_coroutine_threadsafe(self._update_storage(result.id, result, message), loop=self._loop)
        with self._futures_lock:
            self._futures[result.id] = future
        future.add_done_callback(partial(self._cleanup_future, id = result.id))


class GooglePubSub(TaskQueue):
    """ Implements task publishing and consumption using Google Pub/Sub. """

    def __init__(self, project: str = None):
        self._project = project
        if not self._project:
            raise ValueError("Project ID must be provided.")

        self._loop = asyncio.get_running_loop() # Python's 3.10+ get_running_loop.
        self._callback = GooglePubSubCallback(self._loop)
        
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
            logging.exception(f"Error processing future for key {key}: {e}. Resuming publish...")
            self._pub_client.resume_publish(topic, message_id)
        else:
            logging.info(f"Future for message ID: '{message_id}' was successfully published.")

    def _cleanup_sub_future(self, message, key):
        with self._lock_consumer_pool:
            self._consumer_pool.pop(key)
        logging.info(f"Subscription '{key}' was successfully cancelled.")
 
    def _publish(self, message: str, topic: str, request_id: str, tries = 3) -> None:
        topic_name = 'projects/{project}/topics/{topic}'.format(
            project=self._project,
            topic=topic,  
        )
        
        future = self._pub_client.publish(topic_name, message.encode('utf-8')) # This has internal retries and timeout
        logging.info(f"Message with ID: {request_id} was sent to topic: '{topic}'.")

        with self._lock_pub_pool:
            self._pub_pool[request_id] = future

        future.add_done_callback(
                partial(self._cleanup_pub_future, key = request_id, topic = topic))

    def _consume(self, subscription: str, callback: Callable) -> None:
        with self._lock_consumer_pool: # Locking for reading as concurrent writting might cause issues.
            if subscription in self._consumer_pool: # One kind of task has a specific consumer running, there is a low fixed amount of consumers.
                logging.info(f"This subscription {subscription} is already being listened to.") 
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
                    partial(self._cleanup_sub_future, key = subscription))
        logging.info(f"Listening to messages of subscription: '{subscription}'.")


    async def publish_task(self, message: TaskRequest, storage: TaskResponseStorage, tries: int = 3) -> None:
        """ Publishes a task to Google Pub/Sub.
        Args:
            message: The task message.
            storage: The storage to use for task responses.
            tries: The number of retries to attempt if publishing fails.
        Raises:
            ValueError: If the message or storage is invalid.
            UnableToPublishTask: If publishing fails after multiple retries.
        """

        if not isinstance(message, TaskRequest):
            raise ValueError("'message' argument must be derived from TaskRequest.")

        if not isinstance(storage, TaskResponseStorage):
            raise ValueError("'storage' argument must be derived from TaskResponseStorage.")

        task_name = message.task_name
        try:
            topic, sub = GooglePubSubTopicManager.get_topic_sub_pair(task_name)

        except InvalidTaskName as e:
            logging.critical("Invalid task name sent to queue. \
                             Possible causes are: incorrect endpoint configuration,\
                             environment error or TopicManager issue.")
            raise e

        logging.info(f"Publishing task '{task_name}' with ID '{message.id}' to topic '{topic}'.")
        await self._callback.set_storage_to_id(storage, message.id)

        self._publish(message.model_dump_json(), topic, message.id)
        self._consume(sub, self._callback)
        


