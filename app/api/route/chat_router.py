from fastapi import Depends, APIRouter
from sse_starlette import EventSourceResponse
# from starlette.responses import StreamingResponse

from app.deps import get_chat_service
from app.models.schemas.chat import ChatRequest
from app.service.chat_service import ChatService

chat_router = APIRouter(prefix="/chat", tags=["chat"])


@chat_router.post("")
async def chat(message: ChatRequest,
               chat_service: ChatService = Depends(get_chat_service)):
    # return StreamingResponse(
    #     chat_service.upstage_chat(message),
    #     # media_type="text/plain; charset=utf-8"
    #     media_type="text/event-stream; charset=utf-8"
    # )
    return EventSourceResponse(chat_service.upstage_chat(message))
