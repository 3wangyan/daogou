import json
from pathlib import Path
from config.settings import settings
from agents.state import GuideState

# ---------- mock 数据加载 ----------
# 基于文件自身位置定位项目根，避免受启动目录影响
_PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _search_mock(query: dict) -> list[dict]:
    mock_path = _PROJECT_ROOT / "data" / "mock" / "products.json"
    if not mock_path.exists():
        return [{"title": "示例商品（mock 数据缺失）", "price": 0, "platform": "mock"}]
    
    products = json.loads(mock_path.read_text(encoding="utf-8"))
    keyword = query.get("keyword", "").lower()
    max_price = query.get("max_price")
    
    results = []
    for p in products:
        if keyword and keyword not in p["title"].lower():
            continue
        if max_price is not None and p["price"] > max_price:
            continue
        results.append(p)
    
    return results[:10]


# ---------- 真实 MCP 搜索（占位，接 taoke-mcp 时替换）----------
async def _search_mcp(query: dict) -> list[dict]:
    """
    这里接 taoke-mcp。参考配置：
    env:
      TAOBAO_PID: ...
      TAOBAO_SESSION: ...
    
    调用方式取决于你用的 MCP 客户端（langchain-mcp-adapters 或 MCP SDK）。
    工具名通常是 taobao.material.search / jd.goods.query / pdd.goods.search。
    
    返回格式需归一化为:
    [{"title": str, "price": float, "platform": "taobao"|"jd"|"pdd", "url": str}]
    """
    raise NotImplementedError("配置 taoke-mcp 后替换此处")


# ---------- 节点入口 ----------
async def search_products(state: GuideState) -> dict:
    query = state.get("product_query", {})
    
    if settings.TOOL_MODE == "mcp":
        results = await _search_mcp(query)
    else:
        results = _search_mock(query)
    
    return {
        "search_results": results,
        "intent": "recommend",
    }
