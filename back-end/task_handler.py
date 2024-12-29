from task_queue import TaskQueue, queue_register
from tasks import task_factory
from services import Gemini
from functools import partial
from dotenv import load_dotenv
import os

load_dotenv()


if __name__=="__main__":
    queue = queue_register[os.environ["SELECTED_QUEUE_SERVICE"]]
    gemini = Gemini()
    future = queue.consume(partial(task_factory, services=[gemini], queue=queue))
