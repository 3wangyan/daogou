import os
import sys
from pathlib import Path

# 关键：在任何业务模块 import 之前注入占位配置，
# 使 ChatOpenAI 能用假 key 构造成功，测试全程不联网、不花 token。
os.environ.setdefault("OPENAI_API_KEY", "sk-test-dummy-not-real")
os.environ.setdefault("OPENAI_BASE_URL", "http://localhost:9/v1")
os.environ.setdefault("LLM_MODEL", "test-model")
os.environ.setdefault("TOOL_MODE", "mock")

# 把项目根加入 sys.path，使 tests 能 import agents/app/config
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
