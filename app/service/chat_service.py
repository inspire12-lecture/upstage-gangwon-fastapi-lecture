from app.models.schemas.chat import ChatRequest
from app.repository.client.upstage_client import UpstageClient


class ChatService:
    def __init__(self, upstage_client: UpstageClient):
        self.client = upstage_client

    async def upstage_chat(self, message: ChatRequest):
        async for chunk in self.client.chat_streaming(message):
            yield chunk
