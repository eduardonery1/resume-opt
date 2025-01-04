from abc import ABC, abstractmethod
from dotenv import load_dotenv
import google.generativeai as genai
import logging
import os


load_dotenv()
logging.basicConfig(level=logging.DEBUG)

class TaskExecutor(ABC):
    @abstractmethod
    def is_available():
        raise NotImplementedError

    @abstractmethod
    def run_task(task):
        raise NotImplementedError


class Gemini(TaskExecutor):
    def __init__(self):
        genai.configure(api_key=os.environ["GEMINI_API_KEY"])
        self.model = genai.GenerativeModel("gemini-1.5-flash")
    
    def is_available(self):
        return True

    def run_task(self, task):
        response = self.model.generate_content(task.to_prompt())
        return response.text
