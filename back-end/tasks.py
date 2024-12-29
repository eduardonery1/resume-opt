import json
import logging
from pydantic import BaseModel, ValidationError
from services import TaskExecutor
from task_queue import TaskQueue


class Task(BaseModel):
    prompt: str
    params: list[str]
    config: dict[str, str] = {}


class GenerateResumeJSON(Task):
    prompt_params: str = """This text was extracted from a professional resume PDF file: "{}"."""
    prompt: str = """Transform the text into a JSON file filling the following template:\
                        {"name": INSERT NAME, "description": INSERT DESCRIPTION,\
                        "contact": ["contact1", ...],\
                        "education": [{"instution1": NAME, "start_date": START, "end_date": END}],\
                        "experience":[{"company1": NAME, "start_date": START, "end_date": END,\
                        "projects_or_responsabilities": ["project description with person's role and impact with metrics", ...]}]}. """

    def to_prompt(self) -> str:
        return self.prompt_params.format(self.params[0]) + self.prompt


def task_factory(message: str, services: list[TaskExecutor], queue: TaskQueue) -> None:
    """
    Check available LLM services and define callback for task queue.
    """
    logging.info("Running task_factory")
    try:
        try:
            json_raw = str(message.data, encoding="utf8")
            task_json = json.loads(json_raw)
        except json.JSONDecodeError as e:
            logging.error("Invalid queued message.", json_raw)
            message.ack()
            return
        
        try:
            task_model = taskcode_to_task[task_json["task"]]
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
            return 

        task_executor.run_task(task)
        message.ack()
    except Exception as e:
        logging.exception("An unexpected error occured:", str(e))
        raise e

taskcode_to_task = {"resume-information": GenerateResumeJSON }
