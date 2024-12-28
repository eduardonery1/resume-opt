import json
import services
import logging
from pydantic import BaseModel



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

    def to_prompt(self):
        return self.prompt_params.format(self.params[0]) + self.prompt


def task_factory(message, services, queue):
    """
    Check available LLM services and define callback for task queue.
    TODO: Async run on loop using ThreadPoolExecutor
    """
    logging.info("Running task_factory")
    try:
        json_raw = str(message.data, encoding="utf8")
        task_json = json.loads(json_raw)
    except json.JSONDecodeError as e:
        logging.debug("Invalid queued message.", json_raw)
        return

    task_model = taskcode_to_task[task_json["task"]]
    task = task_model(params=[task_json["text"]]) 

    try:
        task_executor = filter(lambda s: s.is_available(), services).__next__()
    except IndexError as e:
        logging.debug("No available services.") 
        message.nack()
        return
    except Exception as e:
        logging.debug("An unexpected error occured.")
        message.nack()
        return

    task_executor.run_task(task)
    message.ack()

taskcode_to_task = {"resume-information": GenerateResumeJSON }
