import os
from typing import Any
from fastapi import APIRouter
from dotenv import load_dotenv
from typing import Union
from ..models.response_model import SuggestedQuestions
import requests

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_ROUTE = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key={GEMINI_API_KEY}"
router = APIRouter(prefix="/helpers", tags=["helpers"])



@router.post("/suggestedQuestions",response_model=SuggestedQuestions)
async def get_suggested_questions(
    latest_question: str,
    assistant_answer: str
) -> SuggestedQuestions:
    prompt = """If the assistant answer has sufficient knowledge, use it to predict the next 3 suggested questions. Otherwise, strictly restrict to these topics: 
    Getting Started with OpenROAD
    Building OpenROAD
    Getting Started with the OpenROAD Flow - OpenROAD-flow-scripts
    Tutorials
    Git Quickstart
    Man pages
  OpenROAD User Guide
  Database
  GUI
  Partition Management
  Restructure
  Floorplan Initialization
  Pin Placement
  Chip-level Connections
  Macro Placement
  Hierarchical Macro Placement
  Tapcell Insertion
  PDN Generation
  Global Placement
  Gate Resizing
  Detailed Placement
  Clock Tree Synthesis
  Global Routing
  Antenna Checker
  Detailed Routing
  Metal Fill
  Parasitics Extraction
  Messages Glossary
  Getting Involved
  Developer's Guide
  Coding Practices
  Logger
  CI
  README Format
  Tcl Format
  Man pages Test Framework
  Code of Conduct
  FAQs

  Your response must be in this exact JSON format:
  {
    "questions": [
      "",
      "",
      ""
    ]
  }
    The first character should be '{' and the last character should be '}'. Do not include any additional text or formatting."""
    try:
        response = requests.post(GEMINI_ROUTE, json={"prompt": prompt})
        return response.json()
    except Exception as e:
        return {"questions": []}
