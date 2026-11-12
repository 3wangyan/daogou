from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from langchain_core.messages import AIMessage
from agents.graph import graph
import json

app = FastAPI(title="智能导购Agent")

class ChatRequest(BaseModel):
    message: str
    thread_id: str = "default"
    user_id: str = "anonymous"

@app.get("/")
def root():
    return {"msg": "智能导购Agent已启动", "docs": "/docs"}

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.post("/chat")
async def chat(req: ChatRequest):
    config = {"configurable": {"thread_id": req.thread_id}}
    input_state = {
        "messages": [{"role": "user", "content": req.message}],
        "user_id": req.user_id,
    }
    
    async def event_stream():
        async for event in graph.astream(input_state, config, stream_mode="values"):
            msgs = event.get("messages", [])
            if msgs and isinstance(msgs[-1], AIMessage):
                content = msgs[-1].content or ""
                yield f"data: {json.dumps({'content': content}, ensure_ascii=False)}\n\n"
        yield "data: [DONE]\n\n"
    
    return StreamingResponse(event_stream(), media_type="text/event-stream")
