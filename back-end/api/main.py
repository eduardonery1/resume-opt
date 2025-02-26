import asyncio
import json
import logging
import os
import uuid
from io import BytesIO

from dotenv import load_dotenv
from fastapi import (BackgroundTasks, FastAPI, File, HTTPException, Response,
                     UploadFile, status)
from fastapi.middleware.cors import CORSMiddleware
from PyPDF2 import PdfReader

from api.task_api import request_task

load_dotenv()

user_data = {}  # Implement JWT

if bool(os.getenv('DEBUG')):
    level = logging.DEBUG
    user_data[os.getenv('DEBUG_TOKEN')] = []
    logging.info('Running on DEBUG mode.')
else:
    level = logging.INFO
    logging.info('Running on Production mode.')

logging.basicConfig(level=level)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get('/auth')
def get_auth():
    token = str(uuid.uuid4())
    user_data[token] = []
    return {'auth': token}


def valid_resume(text: str) -> bool:
    # For prototyping only, isn't reliable in PROD
    keywords = {'experience', 'education', 'skills', 'contact', 'resume'}
    count = 0
    text = text.lower()
    for word in keywords:
        if word in text:
            count += 1
    return count / len(keywords) > 0.5


@app.post('/resume')
async def post_resume(token: str, resume: UploadFile = File(...)):
    if token not in user_data:
        raise HTTPException(status=status.HTTP_403_FORBIDDEN,
                            detail='Invalid token.')

    try:
        contents = await resume.read()
        reader = PdfReader(BytesIO(contents))
    except IOError as e:
        raise HTTPException(status=status.HTTP_400_BAD_REQUEST,
                            detail='Invalid PDF file.')

    pages = [page.extract_text() for page in reader.pages]
    text = ''.join(pages)
    if not valid_resume(text):
        raise HTTPException(
            status=status.HTTP_400_BAD_REQUEST, detail='Not a resume.')

    request = {
        "auth": token,
        "task_name": "resume-optimization",
        "payload": {
            "text": text
        }
    }

    res = await request_task(request)
    return res

