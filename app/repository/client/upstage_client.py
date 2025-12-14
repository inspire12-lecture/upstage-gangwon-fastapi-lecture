import os
from dotenv import load_dotenv
from openai import AsyncOpenAI
from app.models.schemas.chat import ChatRequest

load_dotenv()

class UpstageClient:
    def __init__(self):
        self.api_key = os.getenv("UPSTAGE_API_KEY")
        if not self.api_key:
            raise ValueError("UPSTAGE_API_KEY environment variable is required")
        self.client = AsyncOpenAI(
            api_key=self.api_key,
            base_url="https://api.upstage.ai/v1"
        )

    async def chat_streaming(self, message: ChatRequest):
        """스트리밍 채팅"""
        params = {
            "model": "solar-pro2",
            "messages": [{"role": "user", "content": message.prompt}],
            "stream": True,
        }
        
        if message.tools:
            params["tools"] = message.tools
        
        stream = await self.client.chat.completions.create(**params)
        
        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

