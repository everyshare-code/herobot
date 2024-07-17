import json

from langchain_community.chat_message_histories import SQLChatMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_openai import ChatOpenAI
from langchain_core.prompts import MessagesPlaceholder, ChatPromptTemplate
from langchain_core.messages import HumanMessage
from langchain_core.messages.base import BaseMessage
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain import hub
from backend.model.messages import Message, CustomAIMessage, CustomHumanMessage
from backend.model.flight import SkyscannerAPI
from backend.model.vision import VisionProcessor
from backend.databases.database import Database
from backend.core.config import settings, LLMConfig
from backend.utils.output_parsers import MessageOutputParser
from sqlalchemy import create_engine
from typing import List, Dict, Any, Tuple



class Herobot:
    def __init__(self, db: Database):
        self.vision_api = VisionProcessor()
        self.skyscanner_api = SkyscannerAPI()
        self.llm = ChatOpenAI(model_name="gpt-4o", temperature=1)
        self.output_parser = MessageOutputParser()
        self.db = db
        self.chat_histories: Dict[str, Dict[str, Any]] = {}
        self.chains: Dict[str, Dict[str, Any]] = {}
        self.client_info_store: Dict[str, Dict[str, Any]] = {}
        self.engine = create_engine(settings.SQLITE_CONNECTION_STRING)

    # 프롬프트 로드 함수
    def load_prompt(self) -> Tuple:
        intent_prompt = hub.pull(settings.LANGCHAIN_SYSTEM_PROMPT_NAME)
        flight_prompt = hub.pull(settings.LANGCHAIN_FLIGHT_PROMPT_NAME)
        flight_prompt.append(MessagesPlaceholder(variable_name="history"))
        return (intent_prompt, flight_prompt)

    # 체인 생성 함수
    def create_chain(self, session_id: str):
        intent_prompt, flight_prompt = self.load_prompt()
        self.chains[session_id] = {
            LLMConfig.CHAIN_TYPE_INTENT: (intent_prompt | self.llm | self.output_parser),
            LLMConfig.CHAIN_TYPE_FLIGHT: RunnableWithMessageHistory(
                (flight_prompt | self.llm | self.output_parser),
                get_session_history=lambda session_id: self.get_flight_history(session_id),
                input_messages_key="question",
                history_messages_key="history"
            )
        }
    # 대화 기록을 가져오는 함수
    def get_chat_history(self, session_id: str) -> SQLChatMessageHistory:
        if session_id not in self.chat_histories:
            self.chat_histories[session_id] = {}
        if LLMConfig.CHAIN_TYPE_INTENT not in self.chat_histories[session_id]:
            self.chat_histories[session_id][LLMConfig.CHAIN_TYPE_INTENT] = SQLChatMessageHistory(session_id=session_id, connection=self.engine)
        return self.chat_histories[session_id][LLMConfig.CHAIN_TYPE_INTENT]

    # 항공 기록을 가져오는 함수
    def get_flight_history(self, session_id: str) -> ChatMessageHistory:
        if session_id not in self.chat_histories:
            self.chat_histories[session_id] = {}
        if LLMConfig.CHAIN_TYPE_FLIGHT not in self.chat_histories[session_id]:
            self.chat_histories[session_id][LLMConfig.CHAIN_TYPE_FLIGHT] = ChatMessageHistory()
        return self.chat_histories[session_id][LLMConfig.CHAIN_TYPE_FLIGHT]

    # 프롬프트 생성 함수
    def prompt_func(self, message: Message) -> BaseMessage:
        user_message = HumanMessage(content=message.message)
        return user_message

    # 응답 생성 함수
    def generate_response(self, input_prompt: BaseMessage, session_id: str,
                          chain_type: str = LLMConfig.CHAIN_TYPE_INTENT) -> Message:
        chain = self.chains[session_id][chain_type]
        client_info = self.client_info_store[session_id]
        try:
            print(f"Sending to LLM: {input_prompt.content}")  # 요청 로깅
            response_message = chain.invoke({
                "session_id": session_id,
                "question": input_prompt,
                "client_info": json.dumps(client_info, ensure_ascii=False, indent=4),
            }, {
                "configurable": {"session_id": session_id}
            })
            print(f"response: {response_message}, type: {type(response_message)}")

            # print(f"LLM Response: Type: {response_message.type}, Message: {response_message.message}")  # 응답 로깅
        except Exception as e:
            print(f"Error during LLM invocation: {e}")
            raise
        return response_message

    # 메시지 저장 함수
    def save_messages(self, message: Message, response_message: Message):
        if response_message.sender == 'assist':
            return
        chat_history = self.get_chat_history(message.session_id)
        chat_history.add_message(CustomHumanMessage(**message.dict()))
        chat_history.add_message(CustomAIMessage(**response_message.dict()))

    # 응답 처리 함수
    def response(self, message: Message) -> Message:
        session_id = message.session_id
        if session_id not in self.chains:
            self.create_chain(session_id)
        if session_id not in self.client_info_store:
            self.client_info_store[session_id] = {
                "adults": 1,
                "origin": "",
                "destination": "",
                "origin_location_code": "",
                "destination_location_code": "",
                "departure_date": ""
            }
        user_input = self.prompt_func(message)
        intent_message = self.generate_response(user_input, session_id, LLMConfig.CHAIN_TYPE_INTENT)
        final_message = self.branch_type(intent_message, message)

        self.save_messages(message, final_message)
        return final_message

    # 응답 유형에 따른 분기 처리 함수
    def branch_type(self, intent_message: Message, original_message: Message) -> Message:
        if intent_message.type == "message":
            pass
        elif intent_message.type == 'flight':
            response = self.generate_response(
                input_prompt=self.prompt_func(original_message),
                session_id=intent_message.session_id,
                chain_type=LLMConfig.CHAIN_TYPE_FLIGHT
            )

            client_info = self.client_info_store[original_message.session_id]

            if response.client_info:
                client_info.update(response.client_info)

            if not all(client_info.values()):
                self.client_info_store[original_message.session_id] = client_info
                return response

            flight_info = self.skyscanner_api.get_cheapest_flight_info(self.db, client_info)
            intent_message.message = flight_info

            self.clear_flight_messages(intent_message.session_id)

        elif intent_message.type == 'search':
            if intent_message.image:
                description = self.vision_api.report(intent_message.image)
                intent_message.message = f"\n{description}: user의 이전 질문에 description을 참고해서 한국어로 답변하고 url, image_url을 같이 제공해줘\n답변 예시:\nmessage: 이미지에 나온 위치는 '뉘하운'입니다.\n가장 유사한 이미지가 있는 홈페이지: #url\n가장 유사한 이미지: #image_url"
                intent_message.sender = "assist"
                intent_message.image = ""
                return self.response(intent_message)
        return intent_message

    # 항공 메시지 삭제 함수
    def clear_flight_messages(self, session_id: str):
        self.client_info_store.pop(session_id, None)
        self.chat_histories[session_id][LLMConfig.CHAIN_TYPE_FLIGHT].clear()


if __name__ == "__main__":
    from dotenv import load_dotenv
    import ssl
    load_dotenv()
    ssl._create_default_https_context = ssl._create_unverified_context
    db = Database()
    robot = Herobot(db)
    session_id = input("세션 ID를 입력하세요: ")
    while True:
        user_input = input("질문을 입력하세요 ('종료' 입력 시 종료): ")
        if user_input == '종료':
            break
        message = Message(type="message", sender="user", message=user_input, session_id=session_id)
        response = robot.response(message)
        print("응답:", response)
