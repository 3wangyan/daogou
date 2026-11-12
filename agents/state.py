from typing import TypedDict, Annotated, Literal
from langgraph.graph.message import add_messages

class GuideState(TypedDict):
    messages: Annotated[list, add_messages]
    intent: Literal["ask_more", "search", "recommend", "done"]
    product_query: dict          # {"keyword": str, "max_price": float|None, "preferences": list}
    missing_slots: list[str]     # 还缺哪些信息
    search_results: list[dict]
    user_id: str                 # 长期记忆用
