from sqlalchemy import create_engine, pool
from backend.core.config import settings
from langchain_community.chat_message_histories import SQLChatMessageHistory

engine = create_engine(settings.CONNECTION_STRING, pool_size=5, max_overflow=5)

def get_message_history(session_id: str) -> SQLChatMessageHistory:
    return SQLChatMessageHistory(session_id=session_id, connection=engine, table_name="message")

# Usage
if __name__ == "__main__":
    from sqlalchemy import text
    # engine = create_engine(settings.DB_URL)
    # Session = sessionmaker(bind=engine)
    # session = Session()
    # message = ChatMessageHistory(session_id="aa", user_name="user", content="안녕하세요")
    # session.add(message)
    # session.commit()
    history = get_message_history("aa")
    print(history)