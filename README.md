# 智能导购Agent（smart-guide-agent）

基于LangGraph+大模型的多轮对话导购系统，支持自动追问需求、商品搜索、个性化推荐。

## 快速启动
1. 配置环境变量：复制 `config/.env.example` 为 `.env`，填入你的大模型API Key
2. 安装依赖：
```bash
pip install -r requirements.txt
```
3. 启动服务：
```bash
uvicorn app.main:app --reload --port 8002
```
4. 访问：http://localhost:8002/docs

## 核心流程
1. **clarify（需求澄清）**：自动判断用户需求是否明确，缺品类/预算就追问
2. **search（商品搜索）**：支持mock本地数据/真实MCP电商接口两种模式
3. **recommend（推荐生成）**：基于搜索结果生成个性化推荐话术

## 测试
离线单元测试全部 mock 大模型，不联网、不花 token：

```bash
.venv\Scripts\python.exe -m pytest tests -v
```

覆盖 clarify 三分支（可搜索/需追问/JSON 解析兜底）、search 关键词与预算过滤、
recommend 空结果兜底、图编排编译、`/chat` 流式接口只推 AI 消息。

## 完成度说明（诚实标注）
- ✅ 已实现并跑通：三节点 LangGraph 编排、mock 商品搜索、`/chat` SSE 流式接口、离线测试
- ⏳ 占位待补：`tools/mcp_client.py`（真实淘宝/京东 MCP 接入）、`memory/user_profile.py`（用户长期偏好）、`app/routes`、`app/schemas` 分层
