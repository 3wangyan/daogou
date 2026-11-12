from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from langchain_core.messages import AIMessage
from agents.graph import graph
import json
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(title="智能导购Agent")

# 允许跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=500, description="用户输入")
    thread_id: str = Field(default="default", max_length=50)
    user_id: str = Field(default="anonymous", max_length=50)

@app.get("/")
def root():
    # 返回聊天页面
    return FileResponse("web/index.html")

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.post("/chat")
async def chat(req: ChatRequest):
    try:
        config = {"configurable": {"thread_id": req.thread_id}}
        input_state = {
            "messages": [{"role": "user", "content": req.message}],
            "user_id": req.user_id,
        }
        logger.info(f"收到请求 thread={req.thread_id} msg={req.message[:30]}...")

        async def event_stream():
            try:
                async for event in graph.astream(input_state, config, stream_mode="values"):
                    msgs = event.get("messages", [])
                    if msgs and isinstance(msgs[-1], AIMessage):
                        content = msgs[-1].content or ""
                        if content:
                            yield f"data: {json.dumps({'content': content}, ensure_ascii=False)}\n\n"
                yield "data: [DONE]\n\n"
            except Exception as e:
                logger.error(f"对话流错误: {str(e)}")
                yield f"data: {json.dumps({'content': '抱歉，系统暂时出问题了，请稍后再试'}, ensure_ascii=False)}\n\n"
                yield "data: [DONE]\n\n"

        return StreamingResponse(event_stream(), media_type="text/event-stream")
    except Exception as e:
        logger.error(f"请求处理失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"服务器内部错误: {str(e)}")
