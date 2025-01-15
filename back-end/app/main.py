from fastapi import FastAPI, UploadFile, File, status, Response, BackgroundTasks
from io import BytesIO
from PyPDF2 import PdfReader
from collections import defaultdict
from sys import argv, exit
from dotenv import load_dotenv
from fastapi.responses import StreamingResponse
from queue_publishers import GooglePubSubPublisher
from queue_consumers import GooglePubSubConsumer
from functools import partial
from json import JSONDecodeError
import os
import asyncio
import logging
import json
import uuid
import task_queue



MAX_QUEUE_SIZE = 10000
load_dotenv()
user_data = defaultdict(dict)
queue_publisher = GooglePubSubPublisher()
queue_consumer = GooglePubSubConsumer(os.getenv('GOOGLE_CLOUD_PROJECT'))
task_queue_results = asyncio.PriorityQueue(maxsize=MAX_QUEUE_SIZE)
if bool(os.getenv('DEBUG')):
    logging.basicConfig(level=logging.DEBUG)
    user_data[os.getenv('DEBUG_TOKEN')] = {'order': 0}
    logging.info('Running on DEBUG mode.')
else:
    logging.basicConfig(level=logging.INFO)
    logging.info('Running on Production mode.')
app = FastAPI()

@app.get('/auth')
def get_auth():
    """Generates a unique authentication token.

  Returns:
    tuple: A tuple containing a dictionary with the authentication token and an HTTP status code.  The dictionary has the form `{'auth': token}` where `token` is a string. The status code is always `status.HTTP_200_OK`.

  Raises:
    KeyError: if `user_data` is not defined.

  """
    token = str(uuid.uuid4())
    user_data[token] = {'order': len(user_data)}
    return ({'auth': token}, status.HTTP_200_OK)

def validate_resume_pdf(text: str) -> bool:
    """Validate if the given text resembles a resume.

    Args:
        text: The text to validate (string).  Must not be None or empty.

    Returns:
        True if the text likely represents a resume, False otherwise (bool).

    Raises:
        None.  
    """
    keywords = {'experience', 'education', 'skills', 'contact', 'resume'}
    count = 0
    text = text.lower()
    for word in keywords:
        if word in text:
            count += 1
    return count / len(keywords) > 0.5

@app.post('/resume')
async def post_resume(background_tasks: BackgroundTasks, resume: UploadFile=File(...), token: str=''):
    """Posts a resume for processing.

  Args:
    background_tasks: An instance of BackgroundTasks for asynchronous operations.
    resume: The resume file (PDF) to be processed.  Must be a valid UploadFile object.
    token: The authentication token.  Should be a non-empty string.

  Returns:
    A tuple containing a dictionary and a HTTP status code.  
    The dictionary will contain either the message "Request queued." (HTTP 200) or an error message (HTTP 400 or 500).

  Raises:
    IOError: If the resume file is invalid or queue publishing fails.
  """
    if token not in user_data:
        return ({'error': 'Invalid token.'}, status.HTTP_400_BAD_REQUEST)
    try:
        contents = await resume.read()
        reader = PdfReader(BytesIO(contents))
    except IOError as e:
        return ({'error': 'Invalid PDF File.'}, status.HTTP_400_BAD_REQUEST)
    pages = [page.extract_text() for page in reader.pages]
    text = ''.join(pages)
    if not validate_resume_pdf(text):
        return ({'error': 'Invalid resume PDF.'}, status.HTTP_400_BAD_REQUEST)
    try:
        message = json.dumps({'task': 'resume-information', 'params': text.replace('"', "'"), 'auth': token, 'structured': True})
        await queue_publisher.publish(message)
    except IOError as e:
        logging.exception('Queue publishing service error:', str(e))
        return status.HTTP_500_INTERNAL_SERVER_ERROR

    def callback(message, token, storage):
        """Processes a message, updating storage if authentication is valid.

  Args:
    message: The message to process (assumed to have a `data` attribute containing JSON).
    token: The expected authentication token (str).
    storage: A dictionary-like object to store data (must support item assignment).

  Returns:
    None.

  Raises:
    Exception: If message decoding or data processing fails.  Specific exceptions 
               are logged, but not explicitly re-raised for handling by the caller.
  """
        try:
            data = json.loads(message.data.decode('utf8'))
        except JSONDecodeError as e:
            logging.exception('Invalid message format', str(e), 'Message:', message.data)
            message.ack()
            return
        try:
            logging.debug(f'Current token is {data['auth']}. Expected: {token}')
            if data['auth'] == token:
                storage[data['auth']]['resume-information'] = 'done.'
                message.ack()
                logging.info(f'Message from {token} acknoledged.')
        except KeyError as e:
            logging.exception('No auth key in message.', str(e), data)
            message.ack()
            return
    background_tasks.add_task(queue_consumer.consume, partial(callback, token=token, storage=user_data))
    return ({'text': 'Request queued.'}, status.HTTP_200_OK)

async def get_resume_events(token):
    """Yields resume events for a given token.

Args:
  token: The user token (str).  Must be a valid token.

Returns:
  A generator yielding strings representing resume events.  Each string is a 
  data: message formatted for Server-Sent Events.  May yield "Task not ready" 
  messages before a resume is available.

Raises:
  KeyError: If the token is not found.
"""
    while True:
        try:
            task = user_data[token].get('resume-information', None)
            if task is not None:
                yield f'data: {task}\n\n'
                logging.info(f'Data sent for token {token}.')
                break
            yield "data: {'message': 'Task not ready.'}\n\n"
        except KeyError as e:
            logging.exception(f'KeyError occured while fetching resume information for token: {token}')
            message.ack()
            break
        else:
            logging.info(f'Task not ready for token {token}.')
            await asyncio.sleep(1)

@app.get('/resume')
async def get_resume(token: str):
    """Retrieves resume information for a given token.

    Args:
        token (str): The authentication token. Must be a valid user token.

    Returns:
        Union[StreamingResponse, tuple[dict, int]]: A StreamingResponse object containing resume data if successful, otherwise a tuple containing an error message dictionary and an HTTP status code.  Possible status codes are 200 (success) and 400 (invalid token).

    Raises:
        Exception: If an unexpected error occurs during retrieval.  Returns HTTP 500.
    """
    if token not in user_data:
        return ({'text': 'Invalid token.'}, status.HTTP_400_BAD_REQUEST)
    try:
        return StreamingResponse(get_resume_events(token), media_type='text/event-stream')
    except Exception as e:
        logging.exception('Unexpected error occured while fetching resume information:', str(e))
        return status.HTTP_500_INTERNAL_SERVER_ERROR

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8000)
