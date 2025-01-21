import json
import logging
from pydantic import BaseModel, ValidationError
from abc import abstractmethod, ABC
from typing import Dict, List, Any
from task_executors import TaskExecutor, Gemini

logging.basicConfig(level=logging.INFO)
class Task(BaseModel, ABC):
    prompt: str
    payload: Dict
    
    @abstractmethod
    def to_prompt(self) -> str:
        """ Abstract method to generate the prompt string from the task parameters. """
        raise NotImplementedError


class TaskRequest(BaseModel):
    id: str
    auth: str
    task_name: str
    payload: Dict


class TaskResponse(BaseModel):
    id: str
    payload: Dict


class DummyTask(Task):
    prompt: str = "This is a dummy task. {param1}."
    payload: Dict 
    
    def to_prompt(self) -> str:
        return self.prompt.format(
            param1=self.payload["param1"], 
        )


class TaskManager:
    taskcode_to_task = {"test-task": DummyTask}

    def __init__(self):
        self._executors = [Gemini()]

    def process_task(self, task_request: TaskRequest) -> TaskResponse:
        logging.info("Processing task...")
        try:
            task_class = self.taskcode_to_task.get(task_request.task_name)
            if task_class is None:
                raise ValueError(f"Task {task_request.task_name} not found.")
            
            ex = next(filter(lambda ex: ex.is_available(), self._executors), None)
            if not ex:
                raise ValueError("No available executors")
            logging.info("Found ex.")

            task = task_class(payload=task_request.payload)  # Initialize the task with the payload
            logging.info("Running Executor...")
            processed_payload = ex.run_task(task)
            response = TaskResponse(id=task_request.id, payload={"response": processed_payload})
            return response
        except ValidationError as e:
            logging.error(f"Validation error: {e}")
            raise  # Re-raise the exception for handling at a higher level
        except ValueError as e:
            logging.error(f"Value error: {e}")
            raise
        except Exception as e:
            logging.exception(f"An unexpected error occurred: {e}")
            raise

if __name__=="__main__":
    tm = TaskManager()
    payload = {"param1": "text"}
    res = tm.process_task(
        TaskRequest(id="test", auth="test", task_name="test-task", payload=payload)
    )
    print(res)

