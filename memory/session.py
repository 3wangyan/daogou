from langgraph.checkpoint.memory import MemorySaver
from config.settings import settings

def get_checkpointer():
    if settings.MEMORY_BACKEND == "sqlite":
        from langgraph.checkpoint.sqlite import SqliteSaver
        return SqliteSaver.from_conn_string("checkpoints.db")
    # 默认内存
    return MemorySaver()
