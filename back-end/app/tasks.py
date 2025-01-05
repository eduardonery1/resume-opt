import json
import logging
from pydantic import BaseModel, ValidationError
from abc import abstractmethod
from typing import Dict, List, Any
from task_executors import TaskExecutor
from task_queue import TaskQueue


class Task(BaseModel):
    prompt: str
    params: List[str]
    config: Dict[str, Any] = {}
    
    @abstractmethod
    def to_prompt(self) -> str:
        """ Abstract method to generate the prompt string from the task parameters. """
        raise NotImplementedError

class GenerateResumeJSON(Task):
    prompt: str = """This text was extracted from a professional resume PDF file: "{}".
                        Transform the text into a JSON file filling the following template:\
                        {"name": INSERT NAME, "description": INSERT DESCRIPTION,\
                        "contact": ["contact1", ...],\
                        "education": [{"instution1": NAME, "start_date": START, "end_date": END}],\
                        "experience":[{"company1": NAME, "start_date": START, "end_date": END,\
                        "projects_or_responsabilities": ["project description with person's role and impact with metrics", ...]}]}. """

    def to_prompt(self) -> str:
        """ This method formats the prompt string with the parameters provided. """
        return self.prompt.format(self.params[0])

taskcode_to_task = {"resume": GenerateResumeJSON }
