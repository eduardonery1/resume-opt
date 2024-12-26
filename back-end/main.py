from fastapi import FastAPI, UploadFile, File, status, Response
from io import BytesIO
from pydantic import BaseModel
from PyPDF2 import PdfReader
from producer import connect 
import google.generativeai as genai
import json
import pika

app = FastAPI()

@app.post("/v1/resume-information")
async def extract_resume_information(resume: UploadFile = File(...)):
    try:
        contents = await resume.read()
        reader = PdfReader(BytesIO(contents))
        pages = [ page.extract_text() for page in reader.pages ]
        text = "".join(pages)
        
        return {"text": text}, status.HTTP_200_OK
    
    except IOError as e:
        return {"Invalid PDF File"}, status.HTTP_400_BAD_REQUEST

    except Exception as e:
        return {"error": e}, status.HTTP_500_INTERNAL_SERVER_ERROR




if __name__=="__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
