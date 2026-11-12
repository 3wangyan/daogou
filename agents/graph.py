from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from agents.state import GuideState
from agents.nodes.clarify import clarify
from agents.nodes.search import search_products
from agents.nodes.recommend import recommend

def build_graph():
    builder = StateGraph(GuideState)
    
    builder.add_node("clarify", clarify)
    builder.add_node("search", search_products)
    builder.add_node("recommend", recommend)
    
    builder.add_edge(START, "clarify")
    
    def route_after_clarify(state: GuideState) -> str:
        if state.get("intent") == "ask_more":
            return END
        return "search"
    
    builder.add_conditional_edges("clarify", route_after_clarify, {
        END: END,
        "search": "search",
    })
    builder.add_edge("search", "recommend")
    builder.add_edge("recommend", END)
    
    checkpointer = MemorySaver()
    return builder.compile(checkpointer=checkpointer)

graph = build_graph()
