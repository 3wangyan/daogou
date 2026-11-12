"""智能导购 Agent 离线单元测试。
全部 mock 掉大模型与图执行，不联网、不花 token。
覆盖：clarify 三分支 / search 过滤 / recommend 兜底 / 图编排编译 / chat 流式接口。
"""
import asyncio
import json

from langchain_core.messages import AIMessage, HumanMessage

from agents.nodes import clarify as clarify_mod
from agents.nodes import recommend as recommend_mod
from agents.nodes.search import search_products, _search_mock


# ---------- 测试替身 ----------
class FakeResponse:
    def __init__(self, content):
        self.content = content


class FakeLLM:
    """替身大模型：invoke 返回预设文本，并记录是否被调用。"""
    def __init__(self, content):
        self._content = content
        self.called = False

    def invoke(self, messages):
        self.called = True
        return FakeResponse(self._content)


# ---------- clarify：需求澄清三分支 ----------
def test_clarify_ready_routes_to_search(monkeypatch):
    fake = FakeLLM(json.dumps({
        "ready": True,
        "product_query": {"keyword": "耳机", "max_price": 500, "preferences": []},
    }))
    monkeypatch.setattr(clarify_mod, "llm", fake)
    state = {"messages": [HumanMessage(content="想买个500以内的耳机")], "product_query": {}}
    out = clarify_mod.clarify(state)
    assert out["intent"] == "search"
    assert out["product_query"]["keyword"] == "耳机"
    assert out["missing_slots"] == []
    assert fake.called


def test_clarify_not_ready_asks_more(monkeypatch):
    fake = FakeLLM(json.dumps({
        "ready": False,
        "question": "你想买什么品类的商品？",
        "missing_slots": ["keyword"],
    }))
    monkeypatch.setattr(clarify_mod, "llm", fake)
    state = {"messages": [HumanMessage(content="想买个东西")], "product_query": {}}
    out = clarify_mod.clarify(state)
    assert out["intent"] == "ask_more"
    assert out["missing_slots"] == ["keyword"]
    assert out["messages"][0]["content"] == "你想买什么品类的商品？"


def test_clarify_invalid_json_falls_back(monkeypatch):
    fake = FakeLLM("这不是合法 JSON，是一句普通回复")
    monkeypatch.setattr(clarify_mod, "llm", fake)
    state = {"messages": [HumanMessage(content="随便")], "product_query": {}}
    out = clarify_mod.clarify(state)
    assert out["intent"] == "ask_more"
    assert "keyword" in out["missing_slots"]
    assert out["messages"][0]["content"]


# ---------- search：mock 数据过滤 ----------
def test_search_mock_filters_by_keyword_and_price():
    results = _search_mock({"keyword": "耳机", "max_price": 500})
    assert results, "mock 数据应返回结果"
    for r in results:
        assert "耳机" in r["title"]
        assert r["price"] <= 500


def test_search_mock_keyword_no_match_returns_empty():
    results = _search_mock({"keyword": "宇宙飞船", "max_price": None})
    assert results == []


def test_search_products_returns_results_and_intent():
    state = {"product_query": {"keyword": "耳机", "max_price": None}}
    out = asyncio.run(search_products(state))
    assert out["intent"] == "recommend"
    assert isinstance(out["search_results"], list)
    assert out["search_results"]


# ---------- recommend：推荐生成 ----------
def test_recommend_empty_results_gives_fallback():
    state = {"product_query": {"keyword": "火箭"}, "search_results": [], "messages": []}
    out = recommend_mod.recommend(state)
    assert out["intent"] == "done"
    assert "没有找到" in out["messages"][0]["content"]


def test_recommend_with_results_calls_llm(monkeypatch):
    fake = FakeLLM("推荐索尼WH-1000XM5，降噪效果好，适合通勤。")
    monkeypatch.setattr(recommend_mod, "llm", fake)
    state = {
        "product_query": {"keyword": "耳机"},
        "search_results": [{"title": "索尼WH-1000XM5", "price": 2899, "platform": "jd"}],
        "messages": [HumanMessage(content="推荐个耳机")],
    }
    out = recommend_mod.recommend(state)
    assert out["intent"] == "done"
    assert fake.called
    assert "索尼" in out["messages"][0]["content"]


# ---------- 图编排：结构可编译 ----------
def test_graph_compiles():
    from agents.graph import build_graph
    g = build_graph()
    assert g is not None


# ---------- chat 接口：流式只输出 AI 消息 ----------
def test_chat_stream_yields_only_ai_messages(monkeypatch):
    from fastapi.testclient import TestClient
    import app.main as main_mod

    class FakeGraph:
        async def astream(self, input_state, config, stream_mode=None):
            # 第一轮：末尾是用户消息，应被跳过（这正是修复前会崩溃的地方）
            yield {"messages": [HumanMessage(content="想买耳机")]}
            # 第二轮：末尾是 AI 消息，应被输出
            yield {"messages": [HumanMessage(content="想买耳机"),
                                AIMessage(content="给你推荐几款降噪耳机")]}

    monkeypatch.setattr(main_mod, "graph", FakeGraph())
    client = TestClient(main_mod.app)
    resp = client.post("/chat", json={"message": "想买耳机", "thread_id": "t1"})
    assert resp.status_code == 200
    body = resp.text
    assert "给你推荐几款降噪耳机" in body
    assert "[DONE]" in body
    # 用户自己的话不应作为回复内容被推流
    assert "想买耳机" not in body


def test_health_endpoint():
    from fastapi.testclient import TestClient
    import app.main as main_mod
    client = TestClient(main_mod.app)
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "healthy"}
