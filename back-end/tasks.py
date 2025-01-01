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
        raise NotImplementedError

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


taskcode_to_task = {"resume-information": GenerateResumeJSON }
