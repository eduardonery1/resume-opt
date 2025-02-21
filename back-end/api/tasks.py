import json
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List

from pydantic import BaseModel, ValidationError

from api.task_executors import Gemini, TaskExecutor

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


class ResumeOptimizationTask(Task):
    prompt: str = "Optimize this resume:\n{text}.\n\
            Organize this resume text extracted from a pdf file into logical sections such as Education, Experience, Contact Information, etc.\
            Improve all resposabilities descriptions using metrics, correcting grammar and mantaining a professional tone without making the text much larger.\
            Generate a description that sells a reliable, proactive, and hardworking professional."
    payload: Dict[str, Any]

    def to_prompt(self) -> str:
        return self.prompt.format(text=self.payload["text"])


class TaskManager:
    taskcode_to_task = {"test-task": DummyTask,
                        "resume-optimization": ResumeOptimizationTask}

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

            # Initialize the task with the payload
            task = task_class(payload=task_request.payload)
            logging.info("Running Executor...")
            processed_payload = ex.run_task(task)
            response = TaskResponse(id=task_request.id, payload={
                                    "response": processed_payload})
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


if __name__ == "__main__":
    tm = TaskManager()
    payload = {"param1": "text"}
    res = tm.process_task(
        TaskRequest(id="test", auth="test",
                    task_name="test-task", payload=payload)
    )
    print(res)
