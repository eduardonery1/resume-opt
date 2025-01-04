from fastapi import FastAPI, UploadFile, File, status, Response
from io import BytesIO
from PyPDF2 import PdfReader
from collections import defaultdict
from sys import argv, exit
from dotenv import load_dotenv
from fastapi.responses import StreamingResponse
from queue_publishers import GooglePubSubPublisher
import os
import logging
import json
import uuid 
import task_queue


load_dotenv()
user_data = defaultdict(dict)
queue_publisher = GooglePubSubPublisher(os.environ["GOOGLE_CLOUD_PROJECT"], os.environ["GOOGLE_CLOUD_TOPIC"])
logging.basicConfig(level=logging.DEBUG)

if bool(os.environ["DEBUG"]):
    user_data[os.environ["DEBUG_TOKEN"]]={"order": 0}


app = FastAPI()


@app.get("/auth")
def get_auth():
    token = str(uuid.uuid4())
    user_data[token] = {"order": len(user_data)}
    return {"auth": token}, status.HTTP_200_OK

def validate_resume_pdf(text: str) -> bool:
    keywords = {"experience", "education", "skills", "contact", "resume"}
    count = 0
    text = text.lower()
    for word in keywords:
        if word in text:
            count += 1
    return count/len(keywords) > 0.5

@app.post("/resume-information")
async def post_resume_information(resume: UploadFile = File(...), token: str = ""):
    try:
        if token not in user_data:
            return {"error": "Invalid token."}, status.HTTP_400_BAD_REQUEST

        try:
            contents = await resume.read()
            reader = PdfReader(BytesIO(contents))
        except IOError as e:
            return {"error": "Invalid PDF File."}, status.HTTP_400_BAD_REQUEST
        
        try:
            pages = [ page.extract_text() for page in reader.pages ]
            text = "".join(pages)
            if not validate_resume_pdf(text):
                return {"error": "Invalid resume PDF."}, status.HTTP_400_BAD_REQUEST

            t_queue.publish(json.dumps({"task": "resume-information", 
                               "params": text.replace('"', "'"),
                               "auth": token,
                               "structured": True
                               }) 
                            ) 

            return {"text": "Request queued."}, status.HTTP_200_OK
        except IOError as e:
            logging.exception("Queue service error:", str(e))
            return status.HTTP_500_INTERNAL_SERVER_ERROR

    except Exception as e:
        logging.exception("Unexpected error occured:", str(e))
        return status.HTTP_500_INTERNAL_SERVER_ERROR


async def resume_information_events(token):
    while True:
        try:
            yield str(user_data[token]["resume-information"])
        except KeyError as e:
            logging.exception("KeyError occured while fetching resume information for token:", token)
        finally:
            await asyncio.sleep(.5)

@app.get("/resume-information")
async def get_resume_information(token: str):
    if token not in user_data:
        return {"text": "Invalid token."}, status.HTTP_400_BAD_REQUEST
    return await StreamingResponse(resume_information_events(token), media_type="text/event-stream")



if __name__=="__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
