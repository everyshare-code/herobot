from backend.model.message import Message
from backend.model.flight import AmadeusAPI
from backend.utils.decorators import timestamp
from backend.utils.preprocess import str_to_message
from backend.databases.database import Database
from langchain_openai import ChatOpenAI
from langchain_core.prompts import MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv
from langchain.memory import ConversationBufferMemory
from langchain import hub
from typing import Dict
from datetime import datetime
import json

class Herobot():
    def __init__(self, db: Database):
        self.amadeus_api = AmadeusAPI()
        self.llm = ChatOpenAI(model_name="gpt-4o", temperature=0.1)
        self.output_parser = StrOutputParser()
        self.memory = ConversationBufferMemory(return_messages=True, memory_key="history")
        self.chain = None
        self.db = db
        prompt_name = "everyshare/herobot-system-config"
        self.create_chain(prompt_name)

    def load_prompt(self, prompt_name):
        prompt = hub.pull(prompt_name)
        prompt.append(MessagesPlaceholder(variable_name="history"))
        return prompt

    def create_chain(self, template: str):
        prompt = self.load_prompt(template)
        self.chain = prompt | self.llm | self.output_parser

    def prompt_func(self, message: Message):
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

    def response(self, message: Message) -> Dict:
        memory = self.memory.load_memory_variables({})
        print(f"response: {memory}")
        input_prompt = self.prompt_func(message)

        response = self.chain.invoke(
            {
                "question": input_prompt,
                "today": datetime.now(),
                "history": memory['history'],
            }
        )

        print(response)
        # JSON 파싱
        response_message = str_to_message(response)

        self.memory.save_context(
            {"inputs": json.dumps(
                {
                        "message": message.message,
                        "image": message.image if message.image else ""
                    },
                    ensure_ascii=False)
            },
            {"outputs": response_message.message if response_message.message else ""}
        )
        return self.branch_type(response_message)

    @timestamp
    def branch_type(self, message: Message):
        type = message.type
        if type == 'flight':
            if message.client_info:
                message.message = self.amadeus_api.search_lowest_fare_flight(self.db, message.client_info)
        return message

if __name__ == "__main__":
    import ssl
    load_dotenv()
    ssl._create_default_https_context = ssl._create_unverified_context
    db = Database()
    robot = Herobot(db)
    while True:
        user_input = input("질문을 입력하세요 ('종료' 입력 시 종료): ")
        if user_input == '종료':
            break
        message = Message(sender="user", message=user_input)
        response = robot.response(message)
        print("응답:", response)