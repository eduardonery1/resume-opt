import asyncio
import logging
from abc import ABC, abstractmethod

from tasks import Task, TaskRequest, TaskResponse

__doc__ = """ This module intends to define basic classes, methods and objects necessary to handle TaskRequest incoming from TaskQueues and process them.  
            It also defines the TaskResponse to be sent back to the TaskQueue after processing. 
            It also should orchestrate the TaskExecutors to process the tasks respecting API rate limits. """


class TaskOrchestrator:
    """ Orchestrates the execution of tasks by TaskExecutors, respecting rate limits """

    # in seconds
    def __init__(self, executors: list[TaskExecutor], rate_limit: int = 10, rate_limit_period: int = 60):
        self.executors = executors
        self.rate_limit = rate_limit
        self.rate_limit_period = rate_limit_period
        self.semaphore = asyncio.Semaphore(rate_limit)
        self.logger = logging.getLogger(__name__)

    async def process_task(self, task_request: TaskRequest) -> TaskResponse:
        """ Processes a single task request """
        try:
            # Assuming TaskRequest can be converted to Task
            task = Task(task_request)
            async with self.semaphore:
                # selects an executor based on task type or other criteria
                executor = self._select_executor(task)
                if executor is None:
                    self.logger.error(
                        f"No suitable executor found for task: {task_request}")
                    return TaskResponse(task_request.id, success=False, error="No suitable executor found")

                response = await executor.execute(task)
                return response
        except Exception as e:
            self.logger.exception(
                f"Error processing task {task_request.id}: {e}")
            return TaskResponse(task_request.id, success=False, error=str(e))

    def _select_executor(self, task: Task) -> TaskExecutor:
        """Selects an appropriate executor for the given task.  This is a placeholder and should be customized."""
        # Implement your logic to select the appropriate executor here.
        # For example, you could check the task type or other attributes.
        if self.executors:
            # This selects the first executor in the list.  Replace with your logic.
            return self.executors[0]
        return None

    async def process_task_queue(self, task_queue: asyncio.Queue[TaskRequest]):
        """ Processes a queue of task requests """
        while True:
            task_request = await task_queue.get()
            response = await self.process_task(task_request)
            # Send response back to task queue or other mechanism.  This is a placeholder.
            print(f"Task {task_request.id} processed with response: {response}")
            task_queue.task_done()

# Rate Limiter, TaskQueueResponse
# GooglePubSubRateLimiter, GooglePubSub
# Probably Only one instance of pubsub that manages publishing and consuming,
# a method or class for using it to listen to task topics, create/use a callback (No state beyond the publishing futures)
# async use of publish method as using run_coroutine
# So I need TaskPublisher, TaskConsumer, both use the correspondant TaskQueue through dependency injection
# For google pubsub use a TopicManager to store where to send each thing
# The callbacks shouldn't be too complex, so separating concerns to a queue that handles LLM service execution and seems good.
# TaskExecutorManager or TaskOrchestrator Which would send use rate limiters and a list of available services, to build a response
# then, use a TaskPublisher to send it to a topic of interest
