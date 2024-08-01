from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses  import JSONResponse, RedirectResponse
from tempfile import NamedTemporaryFile, TemporaryDirectory
import os
import boto3
from botocore.exceptions import NoCredentialsError, PartialCredentialsError
from dotenv import load_dotenv
from botocore.client import Config
import httpx
import PyPDF2
import google.generativeai as genai

app = FastAPI()

load_dotenv()

key = os.getenv('GEMINI_API_KEY')

genai.configure(api_key=key)
model = genai.GenerativeModel('gemini-1.5-flash')


def extract_text_from_pdf(pdf_path):
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = ""
            for page_num in range(len(reader.pages)):
                page = reader.pages[page_num]
                text += page.extract_text() + "\n"
        return text
    except Exception as e:
        print(f"An error occurred while extracting text from the PDF: {e}")
        return None
    

def summarize_resume(text):
    try:
        response = model.generate_content(
            
            'The following text is an applicant\'s resume. You must sort it and summarize it into the following categories: years of experience, skills, experiences, projects, awards. Your output should have a very brief format, with the total years of experience listed after "Years of Experience." The list of skills should be listed after "Skills." The list of experiences with brief descriptions should be listed after "Experiences." The list of projects with brief descriptions should be listed after "Projects." A list of the awards should be given after "Awards." Nothing else should be output. Don\'t give any introduction before giving this output, all I need is this output and nothing else. You must include all the fields I mentioned and label them as I specified. If you cannot find information for any of these fields, label it n/a. Here is the resume:' + text,

        )
        return response.text
    except httpx.RequestError as e:
        print(f"An HTTP request error occurred: {e}")
        return None
    except httpx.HTTPStatusError as e:
        print(f"An HTTP status error occurred: {e.response.status_code} - {e.response.text}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred while summarizing the resume: {e}")
        return None
    
session = boto3.session.Session()
client = session.client('s3',
                        endpoint_url=os.getenv('endpoint'), 
                        region_name='nyc3',
                        aws_access_key_id=os.getenv('ACCESS_KEY_ID'),
                        aws_secret_access_key=os.getenv('SECRET_ACCESS_KEY'))

@app.post("/transcribe/")
async def transcribe_audio():
        response = model.generate_content("Hello what is your name")
        response = str(response)
        # returns transcription
        return JSONResponse(content={"transcription": response})

@app.get("/", response_class=RedirectResponse)
async def redirect_to_docs():
    return "/docs"
