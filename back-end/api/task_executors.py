import logging
import os
from abc import ABC, abstractmethod

import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

class TaskExecutor(ABC):
    @abstractmethod
    def is_available():
        raise NotImplementedError

    @abstractmethod
    def run_task(task):
        raise NotImplementedError


class Gemini(TaskExecutor):
    def __init__(self):
        if not os.getenv('GEMINI_API_KEY') and not os.getenv('DEBUG'):
            raise Exception("GEMINI_API_KEY not found in environment variables.")
        api_key = os.getenv('GEMINI_API_KEY')

        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel("gemini-1.5-flash")

    def is_available(self) -> bool:
        return True

    def run_task(self, task) -> str:
        if not self.is_available():
            raise Exception("Gemini API is not available.")

        response = self.model.generate_content(task.to_prompt())
        logging.info(f"Executed task: {task}")
        return response.text
