from typing import AsyncGenerator
from app.models.schemas.chat import ChatRequest
from app.repository.client.upstage_client import UpstageClient
from app.tools import TOOLS

class ChatService:
    def __init__(self, upstage_client: UpstageClient):
        self.client = upstage_client
    
    async def chat(self, message: ChatRequest) -> AsyncGenerator[str, None]:
        """기본 채팅"""
        async for chunk in self.client.chat_streaming(message):
            yield chunk
    
    async def chat_with_tools(self, message: ChatRequest) -> AsyncGenerator[str, None]:
        """도구 지원 채팅"""
        if not message.tools:
            message.tools = TOOLS
        async for chunk in self.client.chat_streaming(message):
            yield chunk
