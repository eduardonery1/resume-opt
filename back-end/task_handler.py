from queue import TaskQueue
from services import Service
from tasks import task_factory

class TaskHandler:
    def __init__(self, queue: TaskQueue, tasks_state, task_executor: Service) -> None:
        self.tasks_state = tasks_state
        self.queue = queue

    async def consume(self):
        await self.queue.consume(lambda queue: task_factory())
