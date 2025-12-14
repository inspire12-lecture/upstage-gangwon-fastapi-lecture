from fastapi import Depends, APIRouter
from sse_starlette import EventSourceResponse
from app.deps import get_chat_service
from app.models.schemas.chat import ChatRequest
from app.service.chat_service import ChatService
from app.tools import TOOLS

chat_router = APIRouter(prefix="/chat", tags=["chat"])

@chat_router.post("/")
async def chat(message: ChatRequest, chat_service: ChatService = Depends(get_chat_service)):
    """기본 채팅"""
    return EventSourceResponse(chat_service.chat(message))

@chat_router.post("/tools")
async def chat_with_tools(message: ChatRequest, chat_service: ChatService = Depends(get_chat_service)):
    """도구 지원 채팅"""
    return EventSourceResponse(chat_service.chat_with_tools(message))

@chat_router.get("/tools")
async def get_tools():
    """사용 가능한 도구 목록"""
    return {"tools": TOOLS}