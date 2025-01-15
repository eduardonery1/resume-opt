from abc import ABC, abstractmethod
from dotenv import load_dotenv
from tasks import Task
import google.generativeai as genai
import logging
import os


load_dotenv()

class TaskExecutor(ABC):
    """ An abstract base class for TaskExecutors. """
    @abstractmethod
    def is_available():
        """ Checks if the TaskExecutor is available. """
        raise NotImplementedError

    @abstractmethod
    def run_task(task):
        """ Runs the given task and returns its result. """
        raise NotImplementedError


class Gemini(TaskExecutor):
    """ A TaskExecutor that uses the Gemini API to run tasks. """
    def __init__(self):
        genai.configure(api_key=os.environ["GEMINI_API_KEY"])
        self.model = genai.GenerativeModel("gemini-1.5-flash")
    
    def is_available(self) -> bool:
        """ Checks if the Gemini API is available. """
        return True

    def run_task(self, task: Task) -> str:
        """ Runs the given task and returns its result. """
        if not self.is_available():
            logging.warning("Gemini API is not available.")
            raise Exception("Gemini API is not available.")

        response = self.model.generate_content(task.to_prompt())
        logging.info(f"Executed task: {task}")
        return response.text
