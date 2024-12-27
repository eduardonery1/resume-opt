from fastapi import FastAPI, UploadFile, File, status, Response
from io import BytesIO
from pydantic import BaseModel
from PyPDF2 import PdfReader
from producer import publish
from collections import defaultdict
from sys import argv
from dotenv import load_dotenv
import google.generativeai as genai
import os
import logging
import json
import uuid 


load_dotenv()
user_data = defaultdict(list)
logging.basicConfig(level=logging.DEBUG)

if len(argv) > 1 and argv[1] == "debug":
    user_data[os.environ["DEBUG_TOKEN"]].append({"order": 0})

app = FastAPI()

@app.get("/auth")
def get_auth():
    token = str(uuid.uuid4())
    user_data[token].append({"order": len(user_data)})
    return token, status.HTTP_200_OK

@app.post("/resume-information")
async def get_resume_information(resume: UploadFile = File(...), token: str = ""):
    try:
        try:
            assert token in user_data
        except AssertionError as e:
            return {"Invalid token."}, status.HTTP_400_BAD_REQUEST

        try:
            contents = await resume.read()
            reader = PdfReader(BytesIO(contents))
        except IOError as e:
            return {"Invalid PDF File."}, status.HTTP_400_BAD_REQUEST
        
        try:
            pages = [ page.extract_text() for page in reader.pages ]
            text = "".join(pages)
            await publish(str({"task": "extract_information", "resume_text": text, "priority": user_data[token][0]["order"]}), "task-queue") 
            return {"Request queued."}, status.HTTP_200_OK
        except IOError as e:
            logging.debug("RabbitMQ error.")
            return status.HTTP_500_INTERNAL_SERVER_ERROR

    except Exception as e:
        logging.debug("Unknow error:", e)
        return status.HTTP_500_INTERNAL_SERVER_ERROR





if __name__=="__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
