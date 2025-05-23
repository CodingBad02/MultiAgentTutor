# app/main.py
from fastapi import FastAPI
from pydantic import BaseModel
import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

app = FastAPI()

# Configure Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in environment variables.")
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-pro') # Or your preferred model

class QueryRequest(BaseModel):
    query: str

class QueryResponse(BaseModel):
    answer: str

@app.get("/")
async def read_root():
    return {"message": "AI Tutor Agent is running!"}

@app.post("/ask_gemini_direct", response_model=QueryResponse)
async def ask_gemini_direct(request: QueryRequest):
    try:
        response = model.generate_content(request.query)
        return QueryResponse(answer=response.text)
    except Exception as e:
        return QueryResponse(answer=f"Error: {str(e)}")

# Placeholder for Tutor Agent logic later
# @app.post("/tutor_ask", response_model=QueryResponse)
# async def tutor_ask(request: QueryRequest):
#     # Here, TutorAgent logic will be called
#     return QueryResponse(answer="Tutor agent will respond here soon.")