from task_queue import TaskQueue, queue_register
from main import user_data
from task_executors import Gemini
from functools import partial
from dotenv import load_dotenv
from tasks import TaskExecutor
from json import JSONDecodeError
import json
import logging
import os
import tasks

load_dotenv()


def message_handler(message ,services: list[TaskExecutor], queue: TaskQueue) -> None:
    """
    Check available LLM services and define callback for task queue.
    """
    logging.info("Running task_factory")
    try:
        try:
            json_raw = str(message.data, encoding="utf8")
            task_json = json.loads(json_raw)
        except JSONDecodeError as e:
            logging.error("Invalid queued message.", json_raw)
            message.ack()
            return
        
        try:
            task_model = tasks.taskcode_to_task[task_json["task"]]
            task = task_model(params=[task_json["params"]]) 
        except KeyError as e:
            logging.error("Incorrect or non-existent task code.")
            message.ack()
            return
        except ValidationError as e:
            logging.error("Invalid message format.")
            message.ack()
            return

        try:
            task_executor = filter(lambda s: s.is_available(), services).__next__()
        except IndexError as e:
            logging.error("No available services.") 
            message.nack()
            return 

        response = task_executor.run_task(task) #perhaps putting this part in message_handler using a observer is better.
        user_data[task_json["auth"]].update({task_json["task"]: response })
        message.ack()
    except Exception as e:
        logging.exception("An unexpected error occured:", str(e))
        message.ack()
        raise e

if __name__=="__main__":
    queue = queue_register[os.environ["SELECTED_QUEUE_SERVICE"]]
    gemini = Gemini()
    
    queue.consume(partial(message_handler, services=[gemini], queue=queue))
