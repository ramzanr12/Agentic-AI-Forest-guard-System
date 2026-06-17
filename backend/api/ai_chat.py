"""AI Chat API."""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from services.ai_service import chat_response, explain_incident

router = APIRouter(prefix="/api/ai", tags=["ai"])


class ChatRequest(BaseModel):
    message: str


class ExplainRequest(BaseModel):
    incident_type: str
    description: str
    zone: str = "Unknown"


@router.post("/chat")
async def chat(req: ChatRequest):
    response = await chat_response(req.message)
    return {"response": response, "type": "text"}


@router.post("/explain")
async def explain(req: ExplainRequest):
    explanation = await explain_incident(req.incident_type, req.description, req.zone)
    return {"explanation": explanation}


@router.get("/daily-summary")
async def daily_summary():
    from services.ai_service import generate_daily_summary
    return {"summary": await generate_daily_summary()}
