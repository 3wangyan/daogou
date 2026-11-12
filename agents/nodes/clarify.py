import json
import logging
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage
from config.settings import settings
from agents.state import GuideState

logger = logging.getLogger(__name__)

llm = ChatOpenAI(
    model=settings.LLM_MODEL,
    api_key=settings.OPENAI_API_KEY,
    base_url=settings.OPENAI_BASE_URL,
    temperature=0.3,
)

CLARIFY_PROMPT = """你是导购助手。根据对话判断用户需求是否足够搜索商品。

当前已收集的信息：
- 品类关键词：{keyword}
- 预算上限：{max_price}
- 偏好条件：{preferences}

判断规则：
1. 如果品类不明确（比如用户只说"想买个东西"），追问品类。
2. 如果品类明确但没说预算，可以追问一次预算。
3. 如果品类和预算都清楚了，或者用户明显不想多说（如"随便，直接推荐"），准备搜索。

返回 JSON：
{{"ready": true, "product_query": {{"keyword": "...", "max_price": null, "preferences": []}}}}
或
{{"ready": false, "question": "追问的话", "missing_slots": ["keyword"]}}
只返回 JSON，不要其他内容。"""

def clarify(state: GuideState) -> dict:
    pq = state.get("product_query", {}) or {}
    
    prompt = CLARIFY_PROMPT.format(
        keyword=pq.get("keyword", "无"),
        max_price=pq.get("max_price", "无"),
        preferences=pq.get("preferences", []),
    )
    
    resp = llm.invoke([SystemMessage(content=prompt)] + state["messages"])
    
    # 容错解析：处理模型输出带```json代码块的情况
    raw = resp.content.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.split("```")[0].strip()
    
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        logger.warning(f"LLM返回非合法JSON: {resp.content[:100]}")
        # LLM 输出不是合法 JSON，追问一次兜底
        return {
            "intent": "ask_more",
            "missing_slots": ["keyword"],
            "messages": [{"role": "assistant", "content": "能再具体说说你想找什么商品吗？"}],
        }
    
    if data.get("ready"):
        return {
            "intent": "search",
            "product_query": data.get("product_query", {}),
            "missing_slots": [],
        }
    else:
        return {
            "intent": "ask_more",
            "missing_slots": data.get("missing_slots", []),
            "messages": [{"role": "assistant", "content": data.get("question", "能再具体说说吗？")}],
        }
