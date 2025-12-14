from pydantic import BaseModel
from typing import Optional, List, Dict, Any

class ToolFunction(BaseModel):
    """도구 함수 정의"""
    name: str
    description: str
    parameters: Dict[str, Any]

class Tool(BaseModel):
    """도구 정의"""
    type: str = "function"
    function: ToolFunction

class ChatRequest(BaseModel):
    """채팅 요청"""
    prompt: str
    tools: Optional[List[Tool]] = None

