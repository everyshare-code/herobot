import ssl
from dotenv import load_dotenv
from langchain_community.chat_message_histories import SQLChatMessageHistory
from langchain_openai import ChatOpenAI
# from langchain_community.chat_models import ChatOllama
# from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import MessagesPlaceholder, ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain import hub
from backend.model.message import Message
from backend.model.flight import SkyscannerAPI
from backend.model.vision import VisionProcessor
from backend.utils.preprocess import str_to_message, resize_image
from backend.databases.database import Database
from datetime import datetime
from typing import List, Dict
from backend.core.config import settings
from sqlalchemy import create_engine

class Herobot:
    def __init__(self, db: Database):
        self.vision_api = VisionProcessor()
        self.skyscanner_api = SkyscannerAPI()
        self.llm = ChatOpenAI(model_name="gpt-4-0125-preview", temperature=0.1)
        self.output_parser = StrOutputParser()
        self.db = db
        self.chat_histories: Dict[str, SQLChatMessageHistory] = {}
        self.chains: Dict[str, RunnableWithMessageHistory] = {}
        self.engine = create_engine(settings.SQLITE_CONNECTION_STRING)

    def load_prompt(self, prompt_name) -> ChatPromptTemplate:
        prompt = hub.pull(prompt_name)
        prompt.append(MessagesPlaceholder(variable_name="history"))
        return prompt

    def create_chain(self, session_id: str):
        prompt = self.load_prompt(settings.LANGCHAIN_PROMPT_NAME)
        chain = prompt | self.llm | self.output_parser
        self.chains[session_id] = RunnableWithMessageHistory(
            chain,
            lambda session_id: self.get_chat_history(session_id),
            input_messages_key="question",
            history_messages_key="history"
        )

    def get_chat_history(self, session_id: str) -> SQLChatMessageHistory:
        if session_id not in self.chat_histories:
            self.chat_histories[session_id] = SQLChatMessageHistory(
                session_id=session_id, connection=self.engine
            )
        return self.chat_histories[session_id]

    # 멀티모달모델용 프롬프트
    # def prompt_func(self, message: Message) -> List[Dict]:
    #     content_parts = [{"type": "text", "text": message.message}]
    #     if message.image:
    #         content_parts.append(
    #             {
    #                 "type": "image_url",
    #                 "image_url": f"data:image/jpeg;base64,{resize_image(message.image)}",
    #             }
    #         )
    #     return [{"role": "user", "content": content_parts}]

    def prompt_func(self, message: Message) -> List[Dict]:
        content_parts = [{"text": message.message}]
        return [{"role": "user", "content": content_parts}]

    def generate_response(self, input_prompt: List[Dict], session_id: str) -> str:
        chain_with_history = self.chains[session_id]
        response = chain_with_history.invoke({"question": input_prompt}, config={'configurable': {'session_id': session_id}})
        return response

    def save_messages(self, message: Message, response_message: Message, session_id: str):
        if response_message.sender == 'assist':
            return
        chat_history = self.get_chat_history(session_id)
        chat_history.add_user_message(message.message)
        chat_history.add_ai_message(response_message.message)

    def response(self, message: Message) -> Message:
        session_id = message.session_id
        if session_id not in self.chains:
            self.create_chain(session_id)

        input_prompt = self.prompt_func(message)

        response = self.generate_response(input_prompt, session_id)
        response_message = str_to_message(response, session_id)

        # Ensure response_message is a Message object
        if isinstance(response_message, dict):
            response_message = Message(**response_message)

        final_message = self.branch_type(response_message)
        self.save_messages(message, final_message, session_id)

        return final_message

    def branch_type(self, message: Message) -> Message:
        if message.type == 'flight':
            if message.client_info:
                message.message = self.skyscanner_api.get_cheapest_flight_info(self.db, message.client_info)
        elif message.type == 'search':
            if message.message == "":
                description = self.vision_api.report(message.image)
                message.message = f"""\n{description}:user의 이전 질문에 description을 참고해서 한국어로 답변하고 url, image_url을 같이 제공해줘
                답변 예시: 
                message: 이미지에 나온 위치는 '뉘하운'입니다.
                        가장 유사한 이미지가 있는 홈페이지: #url
                        가장 유사한 이미지: #image_url              
                """
                message.sender = "assist"
                message.image = ""
                return self.response(message)
        return message


if __name__ == "__main__":
    load_dotenv()
    ssl._create_default_https_context = ssl._create_unverified_context
    db = Database()
    robot = Herobot(db)
    session_id = input("세션 ID를 입력하세요: ")
    while True:
        user_input = input("질문을 입력하세요 ('종료' 입력 시 종료): ")
        if user_input == '종료':
            break
        message = Message(type="text", sender="user", message=user_input, session_id=session_id)
        response = robot.response(message)
        print("응답:", response)
