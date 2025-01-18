from abc import ABC, abstractmethod
from asyncio import Lock, Queue
from tasks import TaskResponse
from typing import Optional
from dotenv import load_dotenv
from pydantic import ValidationError
from utils import RetryError, exp_backoff
import os
import logging
import asyncio

load_dotenv()

class StorageError(Exception):
    """ Base class for all storage errors. """
    pass

class NotFoundError(StorageError):
    """ Raised when a requested item is not found. """
    pass


class RedundantResponseError(StorageError):
    """ Raised when a response is attempted to be updated after it has already been retrieved. """
    pass


class TaskResponseStorage(ABC):
    """ Abstract base class for storing TaskResponse objects.
        There is only one TaskResponse per ID, as they are request IDs. 
    """
    @abstractmethod
    async def create(id: str) -> None:
        raise NotImplementedError
    
    @abstractmethod
    async def read(id: str) -> Optional[TaskResponse]:
        raise NotImplementedError
    
    @abstractmethod
    async def update(id: str, raw_data: bytes | TaskResponse) -> None:
        raise NotImplementedError

    @abstractmethod
    async def delete(id: str) -> None:
        raise NotImplementedError


class DictStorage(TaskResponseStorage):
    """ Use this for staging as it dosen't scale in prod. """
    
    def __init__(self, maxsize: int = 1) -> None:
        if bool(os.getenv('PROD')):
            raise EnvironmentError("DictStorage should not be used in production.")
        
        self._id_to_result_queue = {} 
        self._lock = Lock()
        self._maxsize = maxsize

    async def create(self, id: str) -> None:
        """ Sets the result queue for the given ID.

        Args:
            id: The ID of the result queue.
            queue: The result queue to set.
        """
        if not isinstance(id, str):
            logging.error(f"DictStorage.update: 'id' must be a string. Received: {type(id)}.")
            raise TypeError("DictStorage.update: 'id' must be a string.")
        queue = Queue(maxsize=1)

        async with self._lock:
            self._id_to_result_queue.update({id: queue})
        logging.info(f"DictStorage.create: Created queue for ID: '{id}'.")

    async def read(self, id: str):
        logging.info(f"DictStorage.read: Reading from ID: '{id}'.")
        async with self._lock:
            logging.info(f"DictStorage.read: Acquired _lock for '{id}'.")
            queue = self._id_to_result_queue.get(id, None)
        logging.info(f"DictStorage.read: Released _lock for '{id}'.")

        if not queue:
            raise NotFoundError(f"Result queue for ID {id} not found.")
        
        try:
            result = await queue.get()
        except RetryError:
            logging.exception(f"DictStorage.read: Timeout waiting for result from ID: '{id}'.")
            raise
        except Exception as e:
            logging.exception("DictStorage.read: Unexpected exception:", str(e))
            raise e
        
        queue.task_done()
        
        return result

    async def update(self, request_id: str, raw_data: bytes | TaskResponse) -> None:
        """ Adds data to the result queue associated with the given ID.

        Args:
            id: The ID of the result queue.
            data: The data to add to the queue.

        Raises:
            KeyError: If the result queue for the given ID does not exist.
            QueueFull: If the result queue for the given ID is full. 
        """
        logging.info(f"DictStorage.update: Updating for ID: '{request_id}'.")

        if not isinstance(raw_data, TaskResponse):
            try:
                data = TaskResponse.model_validate_json(raw_data)

            except ValidationError:
                logging.exception(f"DictStorage.update: Invalid TaskResponse received from ID: {request_id}:\n{raw_data}")
                raise ValidationError(f"Invalid TaskResponse received from ID: {request_id}")
        else:
            data = raw_data

        async with self._lock:
            logging.info(f"DictStorage.update: Acquiring _lock for ID: '{request_id}'.")
            if request_id not in self._id_to_result_queue:
                logging.exception(f"DictStorage.update: Result queue for ID {request_id} not found.")
                raise NotFoundError(f"Result queue for ID {request_id} not found.")
            queue = self._id_to_result_queue[request_id] # Avoid modification when acessing it
        logging.info(f"DictStorage.update: Released _lock for ID: '{request_id}'.")

        if queue.full():
            logging.warning(f"DictStorage.update: Attempting to update '{request_id}' which already has a response.")
            raise RedundantResponseError(f"Result queue for ID {request_id} is full.")
        
        queue.put_nowait(data)
        logging.info(f"DictStorage.update: Updated 'TaskResponse' for ID: '{request_id}'.")
                
    async def delete(self, id: str) -> None:
        """ Removes the result queue associated with the given ID.

        Args:
            id: The ID of the result queue to remove.

        Raises:
            KeyError: If the result queue for the given ID does not exist.
        """
        logging.info(f"DictStorage.delete: Deleting from ID: '{id}'.")
        async with self._lock:
            if id not in self._id_to_result_queue:
                logging.warning(f"Tried to remove result queue for ID {id}, but it doesn't exist.")
                raise NotFoundError(f"Result queue for ID {id} not found.")

            self._id_to_result_queue.pop(id)
        logging.info(f"DictStorage.delete: Deleted queue for ID: '{id}'.")


