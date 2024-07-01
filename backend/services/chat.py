from backend.model.message import Message
from backend.model.flight import AmadeusAPI
from backend.model.vision import VisionProcessor
from backend.utils.preprocess import str_to_message, resize_image
from backend.databases.database import Database
from langchain_openai import ChatOpenAI
from langchain_core.prompts import MessagesPlaceholder, ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv
from langchain.memory import ConversationBufferMemory
from langchain import hub
from datetime import datetime
from typing import List


class Herobot:
    def __init__(self, db: Database):
        self.vision_api = VisionProcessor()
        self.amadeus_api = AmadeusAPI()
        self.llm = ChatOpenAI(model_name="gpt-4o", temperature=0.1, max_tokens=4096)
        self.output_parser = StrOutputParser()
        self.memory = ConversationBufferMemory(return_messages=True, memory_key="history")
        self.chain = None
        self.db = db
        prompt_name = "everyshare/herobot-system-config"
        self.create_chain(prompt_name)

    def load_prompt(self, prompt_name) -> ChatPromptTemplate:
        prompt = hub.pull(prompt_name)
        prompt.append(MessagesPlaceholder(variable_name="history"))
        return prompt

    def create_chain(self, template: str):
        prompt = self.load_prompt(template)
        self.chain = prompt | self.llm | self.output_parser

    def prompt_func(self, message: Message) -> List:
        content_parts = [{"type": "text", "text": message.message}]
        if message.image:
            content_parts.append(
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{message.image}"
                    },
                }
            )

        return [{"role": "user", "content": content_parts}]

    def response(self, message: Message) -> Message:
        memory = self.memory.load_memory_variables({})
        input_prompt = self.prompt_func(message)

        # 디버깅을 위해 프롬프트 출력
        print(f"input_prompt: {input_prompt}")

        response = self.chain.invoke(
            {
                "question": input_prompt,
                "history": memory['history'],
            }
        )
        # JSON 파싱
        response_message = str_to_message(response, message.image)
        self.memory.save_context(
            {"inputs":f"""
                {{
                    "message": {message.message},
                    "image": {message.image if message.image else ""}
                }}
            """
            },
            {"outputs": response_message.message if response_message.message else ""}
        )
        return self.branch_type(response_message)

    def branch_type(self, message: Message) -> Message:
        type = message.type
        if type == 'flight':
            if message.client_info:
                message.message = self.amadeus_api.search_lowest_fare_flight(self.db, message.client_info)
        elif type == 'search':
            if message.message == "unidentified":
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
    import ssl
    load_dotenv()
    ssl._create_default_https_context = ssl._create_unverified_context
    filename = "/Users/everyshare/PycharmProjects/herobot/backend/datas/room3.jpeg"
    db = Database()
    robot = Herobot(db)

    while True:
        user_input = input("질문을 입력하세요 ('종료' 입력 시 종료): ")
        if user_input == '종료':
            break
        resized_image = resize_image(filename)
        message = Message(sender="user", message=user_input, image=resized_image)
        response = robot.response(message)
        print("응답:", response)