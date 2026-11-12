from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage
from config.settings import settings
from agents.state import GuideState

llm = ChatOpenAI(
    model=settings.LLM_MODEL,
    api_key=settings.OPENAI_API_KEY,
    base_url=settings.OPENAI_BASE_URL,
    temperature=0.5,
)

RECOMMEND_PROMPT = """你是导购助手。根据用户需求，从搜索结果中推荐 1-3 款商品。

用户需求：{query}
搜索结果：
{products}

要求：
1. 优先推荐符合预算和偏好的商品。
2. 每款商品说一句推荐理由，不要罗列所有参数。
3. 语气自然、有帮助，像朋友给建议。
4. 如果结果都不太匹配，如实告诉用户，并建议放宽哪个条件。
"""

def recommend(state: GuideState) -> dict:
    query = state.get("product_query", {})
    results = state.get("search_results", [])
    
    if not results:
        return {
            "intent": "done",
            "messages": [{"role": "assistant", "content": "没有找到匹配的商品，要不放宽一下预算或换个关键词试试？"}],
        }
    
    products_text = "\n".join([
        f"- {p['title']} | ¥{p['price']} | {p.get('platform', '')}"
        for p in results
    ])
    
    prompt = RECOMMEND_PROMPT.format(query=query, products=products_text)
    resp = llm.invoke([SystemMessage(content=prompt)] + state["messages"])
    
    return {
        "intent": "done",
        "messages": [{"role": "assistant", "content": resp.content}],
    }
