from fastapi import FastAPI, UploadFile, File, status, Response, BackgroundTasks
from io import BytesIO
from PyPDF2 import PdfReader
from dotenv import load_dotenv
import os
import asyncio
import logging
import json
import uuid
from task_api import request_task


load_dotenv()
user_data = {} # Implement JWT

if bool(os.getenv('DEBUG')):
    logging.basicConfig(level=logging.DEBUG)
    user_data[os.getenv('DEBUG_TOKEN')] = []
    logging.info('Running on DEBUG mode.')
else:
    logging.basicConfig(level=logging.INFO)
    logging.info('Running on Production mode.')

app = FastAPI()

@app.get('/auth')
def get_auth():
    token = str(uuid.uuid4())
    user_data[token] = []
    return ({'auth': token}, status.HTTP_200_OK)

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
async def post_resume(token: str, resume: UploadFile=File(...)):
    if token not in user_data:
        return {'error': 'Invalid token.'}, status.HTTP_400_BAD_REQUEST

    try:
        contents = await resume.read()
        reader = PdfReader(BytesIO(contents))
    except IOError as e:
        return {'error': 'Invalid PDF File.'}, status.HTTP_400_BAD_REQUEST

    pages = [page.extract_text() for page in reader.pages]
    text = ''.join(pages)
    if not valid_resume(text):
        return {"text": "Invalid resume pdf."}, status.HTTP_400_BAD_REQUEST
    
    request = {
        "auth": token, 
        "task_name": "resume-optimization",
        "payload":{ 
            "text": text 
        }
    }

    res = await request_task(request)
    return res

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8000)
