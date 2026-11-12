import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # LLM
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")
    
    # 工具模式: "mock" 或 "mcp"
    TOOL_MODE = os.getenv("TOOL_MODE", "mock")
    
    # taoke-mcp 配置（TOOL_MODE=mcp 时需要）
    TAOBAO_PID = os.getenv("TAOBAO_PID", "")
    TAOBAO_SESSION = os.getenv("TAOBAO_SESSION", "")
    JD_KEY = os.getenv("JD_KEY", "")
    JD_PID = os.getenv("JD_PID", "")
    
    # 记忆: "memory" 或 "sqlite" 或 "postgres"
    MEMORY_BACKEND = os.getenv("MEMORY_BACKEND", "memory")

settings = Settings()
