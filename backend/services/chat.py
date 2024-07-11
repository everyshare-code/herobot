from langchain_community.chat_message_histories import SQLChatMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_openai import ChatOpenAI
from langchain_core.prompts import MessagesPlaceholder, ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain import hub
from backend.model.messages import Message, CustomAIMessage, CustomHumanMessage
from backend.model.flight import SkyscannerAPI
from backend.model.vision import VisionProcessor
from backend.utils.utils import str_to_message, format_search_results, process_messages
from backend.databases.database import Database
from backend.core.config import settings
from sqlalchemy import create_engine, text
import json
from typing import List, Dict, Any


class Herobot:
    def __init__(self, db: Database):
        self.vision_api = VisionProcessor()
        self.skyscanner_api = SkyscannerAPI()
        self.llm = ChatOpenAI(model_name="gpt-4o", temperature=1)
        self.output_parser = PydanticOutputParser(pydantic_object=Message)  # PydanticOutputParser에 출력 유형을 지정합니다.
        self.db = db
        self.chat_histories: Dict[str, SQLChatMessageHistory] = {}
        self.chains: Dict[str, Dict[str, Any]] = {}
        self.engine = create_engine(settings.SQLITE_CONNECTION_STRING)

    def initialize_vector_store(self, session_id: str):
        sql = text(f"SELECT MESSAGE FROM MESSAGE_STORE WHERE SESSION_ID = :session_id")
        with self.engine.connect() as connection:
            result = connection.execute(sql, {"session_id": session_id})
            messages = [json.loads(row[0]) for row in result]
            print(messages)
            message_texts = process_messages(messages)

    def load_prompt(self, prompt_name) -> ChatPromptTemplate:
        prompt = hub.pull(prompt_name)
        prompt.append(MessagesPlaceholder(variable_name="history"))
        return prompt

    def create_chain(self, session_id: str):
        prompt = self.load_prompt(settings.LANGCHAIN_PROMPT_NAME)
        chain = prompt | self.llm | self.output_parser
        self.chains[session_id] = {
            'main': RunnableWithMessageHistory(
                chain,
                lambda session_id: self.get_chat_history(session_id),
                input_messages_key="question",
                history_messages_key="history"
            ),
            'flight': RunnableWithMessageHistory(
                chain,
                lambda session_id: self.get_flight_history(session_id),
                input_messages_key="question",
                history_messages_key="history"
            )
        }

    def get_flight_history(self, session_id: str):
        if 'flight' not in self.chains.get(session_id, {}):
            self.chains[session_id]['flight'] = ChatMessageHistory()
        return self.chains[session_id]['flight']

    def get_chat_history(self, session_id: str) -> SQLChatMessageHistory:
        if session_id not in self.chat_histories:
            self.chat_histories[session_id] = SQLChatMessageHistory(session_id=session_id, connection=self.engine)
        return self.chat_histories[session_id]

    def prompt_func(self, message: Message) -> List[Dict]:
        prompt = message.message
        if message.history and message.sender == 'assist':
            prompt += f' {message.history}: 이 내용을 참고해서 답변해줘'
        return [{"role": "user", "content": [{"text": prompt}]}]

    def generate_response(self, input_prompt: List[Dict], session_id: str, chain_type='main') -> Message:
        chain_with_history = self.chains[session_id][chain_type]
        response_message = chain_with_history.invoke(
            {
                "session_id": session_id,
                "question": input_prompt
            },
            {
                "configurable": {"session_id": session_id}
            }
        )
        # session_id를 추가한 후 PydanticOutputParser를 사용하여 Message 객체로 변환합니다.
        # response_message = self.output_parser.parse_result(response)
        response_message.session_id = session_id  # session_id를 추가합니다.
        return response_message

    def save_messages(self, message: Message, response_message: Message, session_id: str):
        if response_message.sender == 'assist':
            return
        chat_history = self.get_chat_history(session_id)
        chat_history.add_message(CustomHumanMessage(**message.dict()))
        chat_history.add_message(CustomAIMessage(**response_message.dict()))

    def response(self, message: Message) -> Message:
        session_id = message.session_id
        if session_id not in self.chains:
            self.create_chain(session_id)

        input_prompt = self.prompt_func(message)
        response_message = self.generate_response(input_prompt, session_id)
        final_message = self.branch_type(response_message, message)

        self.save_messages(message, final_message, session_id)
        return final_message

    def semantic_search(self, session_id: str, query: str, k: int = 5, score_threshold: float = 0.5) -> str:
        results = self.vector_store.semantic_search(session_id, query, k, score_threshold)
        if not results:
            return "이전 대화 내역에서 관련 정보를 찾지 못했습니다."
        else:
            return format_search_results(results)

    def branch_type(self, response_message: Message, original_message: Message) -> Message:
        if response_message.type == 'flight' and response_message.client_info:
            flight_info = self.skyscanner_api.get_cheapest_flight_info(self.db, response_message.client_info)
            response_message.message = flight_info
            self.clear_flight_messages(original_message.session_id)
        elif response_message.type == 'search' and response_message.message == "":
            description = self.vision_api.report(response_message.image)
            response_message.message = f"\n{description}: user의 이전 질문에 description을 참고해서 한국어로 답변하고 url, image_url을 같이 제공해줘\n답변 예시:\nmessage: 이미지에 나온 위치는 '뉘하운'입니다.\n가장 유사한 이미지가 있는 홈페이지: #url\n가장 유사한 이미지: #image_url"
            response_message.sender = "assist"
            response_message.image = ""
            return self.response(response_message)
        elif response_message.type == 'history' and not response_message.history:
            response_message.sender = "assist"
            response_message.history = self.semantic_search(original_message.session_id, response_message.message)
            prompt = self.prompt_func(response_message)
            response_message.message = self.generate_response(input_prompt=prompt, session_id=original_message.session_id)
        return response_message

    def clear_flight_messages(self, session_id: str):
        chat_history = self.get_chat_history(session_id)
        messages = chat_history.get_messages()
        non_flight_messages = [msg for msg in messages if not (hasattr(msg, 'additional_kwargs') and msg.additional_kwargs.get('type') == 'flight')]
        chat_history.clear()
        chat_history.add_messages(non_flight_messages)


if __name__ == "__main__":
    from dotenv import load_dotenv
    import ssl
    load_dotenv()
    ssl._create_default_https_context = ssl._create_unverified_context
    db = Database()
    robot = Herobot(db)
    session_ids = input("세션 ID를 입력하세요: ")
    while True:
        user_input = input("질문을 입력하세요 ('종료' 입력 시 종료): ")
        if user_input == '종료':
            break
        message = Message(type="text", sender="user", message=user_input, session_id=session_ids)
        response = robot.response(message)
        print("응답:", response)
