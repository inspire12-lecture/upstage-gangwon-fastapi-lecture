"""간단한 tool calling 구현 (강의용)"""
from app.models.schemas.chat import Tool, ToolFunction

# 간단한 도구 정의
TOOLS = [
    Tool(
        type="function",
        function=ToolFunction(
            name="get_weather",
            description="날씨 정보 조회",
            parameters={
                "type": "object",
                "properties": {"location": {"type": "string"}},
                "required": ["location"]
            }
        )
    ),
    Tool(
        type="function",
        function=ToolFunction(
            name="add_numbers", 
            description="두 숫자 더하기",
            parameters={
                "type": "object",
                "properties": {
                    "a": {"type": "number"},
                    "b": {"type": "number"}
                },
                "required": ["a", "b"]
            }
        )
    )
]


def execute_tool(name: str, args: dict) -> str:
    """도구 실행"""
    if name == "get_weather":
        location = args.get("location", "")
        return f"{location} 날씨: 맑음, 22도"
    
    elif name == "add_numbers":
        a = args.get("a", 0)
        b = args.get("b", 0) 
        return f"{a} + {b} = {a + b}"
    
    return "알 수 없는 도구입니다"