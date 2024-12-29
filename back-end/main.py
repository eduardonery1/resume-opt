from fastapi import FastAPI, UploadFile, File, status, Response
from io import BytesIO
from PyPDF2 import PdfReader
from collections import defaultdict
from sys import argv, exit
from dotenv import load_dotenv
import os
import logging
import json
import uuid 
import task_queue


load_dotenv()
user_data = defaultdict(list)
logging.basicConfig(level=logging.DEBUG)

if bool(os.environ["DEBUG"]):
    user_data[os.environ["DEBUG_TOKEN"]].append({"order": 0})

try:
    t_queue = task_queue.queue_register[os.environ["SELECTED_QUEUE_SERVICE"]]
except KeyError as e:
    logging.debug("SELECTED_QUEUE_SERVICE IS INVALID! EXITING...")
    exit()

app = FastAPI()

@app.get("/auth")
def get_auth():
    token = str(uuid.uuid4())
    user_data[token].append({"order": len(user_data)})
    return {"auth": token}, status.HTTP_200_OK

@app.post("/resume-information")
async def get_resume_information(resume: UploadFile = File(...), token: str = ""):
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
            t_queue.publish(json.dumps({"task": "resume-information", 
                               "params": text.replace('"', "'"),
                               "config": {"storage": "upstash_redis"},
                               "auth": token,
                               "structured": True,
                               "priority": user_data[token][0]["order"]}) 
                            ) 
            return {"text": "Request queued."}, status.HTTP_200_OK
        except IOError as e:
            logging.exception("Queue service error:", str(e))
            return status.HTTP_500_INTERNAL_SERVER_ERROR

    except Exception as e:
        logging.exception("Unexpected error occured:", str(e))
        return status.HTTP_500_INTERNAL_SERVER_ERROR



if __name__=="__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
