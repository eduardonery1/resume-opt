import asyncio
import logging
import uuid
from asyncio import QueueFull
from storages import DictStorage, TaskResponseStorage
from tasks import TaskRequest, TaskResponse
from dependency_injector import containers, providers
from dependency_injector.wiring import Provide, inject
from pydantic import ValidationError
from typing import Dict, Any
from exceptions import UnableToFetchResultError, InvalidTaskName, UnableToPublishTask
from task_queue import GooglePubSubTaskPublisher
from functools import partial
from utils import exp_backoff
from threading import Lock


class Container(containers.DeclarativeContainer):
    config = providers.Configuration()
    queue = providers.ThreadSafeSingleton(GooglePubSubTaskPublisher)
    result_storage = providers.ThreadSafeSingleton(DictStorage)

@inject
async def request_task(request: Dict, 
                       storage = Provide[Container.result_storage], 
                       queue = Provide[Container.queue], 
                       timeout: float = 5, tries: int = 5) -> Dict:
    """ Requests a task from the queue and waits for the result.

    Args:
        request: A dictionary containing the task request.  Must include 'auth' and 'task_name' keys.
        storage: The ResultStorage instance to use.  Injected via dependency injection.
        queue: The TaskQueue instance to use. Injected via dependency injection.
        timeout: The timeout for waiting for the result.
        tries: The number of retries to attempt before giving up.

    Returns:
        A dictionary containing the task result.

    Raises:
        TypeError: If the request is not a dictionary.
        ValidationError: If the request is invalid.
        KeyError: If a required key is missing from the request.
        UnableToFetchResultError: If the result cannot be fetched after multiple retries.
        Exception: For any other unexpected errors.
    """

    logging.debug(f"Current request: {request}")
    if not isinstance(request, dict):
        raise TypeError("Request must be a dictionary.")

    if not isinstance(storage, TaskResponseStorage):
        raise TypeError("'storage' paramenter must be derived from 'TaskResponseStorage' class.")

    request_id = str(uuid.uuid4()) 
    request.update({"id": request_id})

    try:
        request_obj = TaskRequest(**request)
    except ValidationError as e:
        logging.error(f"Invalid request: {e}")
        raise e
    except KeyError as e:
        logging.error(f"Missing key in request: {e}")
        raise e

    auth = request_obj.auth
    task_name = request_obj.task_name

    await storage.create(request_id)

    try: 
        await queue.publish_task(request_obj, storage)
    except UnableToPublishTask as e:
        logging.exception(f"Unable to publish task. Auth: {auth}, Request ID: {request_id}")
        raise e
    
    else:
        try:
            result = await storage.read(request_id)
            logging.info("Request sucessfully handled.")
        except Exception as e:
            raise UnableToFetchResultError("After several tries the system was unable to fetch results.", str(e))

    finally:
        try:
            await storage.delete(request_id)
        except Exception as e:
            logging.exception(f"Unable to delete {request_id}.", str(e))
            pass

    return result


container = Container()
container.wire(modules=[__name__])

if __name__=="__main__":
    import sys
    import time
    logging.basicConfig(level=logging.INFO)

    async def single_request(i):
        try:
            request = {
                "auth": "test_auth",
                "task_name": "test-task",
                "payload": {"param1": str(i)}
            }
            #logging.info(f"Requesting {i}...")
            result = await request_task(request)
            print(f"Task result: {result}")

        except (UnableToFetchResultError, InvalidTaskName, ValidationError, KeyError) as e:
            logging.error(f"Error processing task: {e}")
            sys.exit(1)

        except Exception as e:
            logging.exception(f"An unexpected error occurred: {e}")
            sys.exit(1)
    
    async def main():
        loop = asyncio.get_running_loop()
        for n in [100]:
            tasks = [loop.create_task(single_request(i)) for i in range(n)]
            start = time.time()
            await asyncio.gather(*tasks)
            end = time.time()
            print(f"Total time taken {n} requests: {end - start:.4f} seconds. AVG time per req: {(end - start) / n:.6f} seconds")

    asyncio.run(main())
        
