import json
import services
from pydantic import BaseModel




class Task(BaseModel):
    prompt: str
    params: list[str]


class ParseResumeJSON(Task):
    prompt: str = """This text was extracted from a professional resume PDF file: "{}".\
            Transform the text into a JSON file filling the following template:\
            {"name": INSERT NAME, "description": INSERT DESCRIPTION,\
            "contact": ["contact1", ...],\
            "education": [{"instution1": NAME, "start_date": START, "end_date": END}],\
            "experience":[{"company1": NAME, "start_date": START, "end_date": END,\
            "projects_or_responsabilities": ["project description with person's role and impact with metrics", ...]}]}. """


def task_factory(message, queue):
    """
    Check available LLM services and define callback for task queue.
    """
    task_json = json.loads(str(message.data, 'utf-8'))
    task_model = taskcode_to_model[task_json["code"]]
    task = task_model(params={"structured": "JSON", "texts": [task_json["text"]]}) 


taskcode_to_model = {"resume-information": ParseResumeJSON}
