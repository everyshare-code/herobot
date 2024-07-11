import re
import json
from typing import Optional, List, Dict
from backend.model.messages import Message, CustomHumanMessage, CustomAIMessage
from langchain_core.messages import BaseMessage
from backend.utils.vision_util import save_image_from_base64

def str_to_message(response: str, session_id: str) -> Optional[Message]:
    try:
        # 정규 표현식을 사용하여 중괄호 {} 영역만 추출
        match = re.search(r'\{.*\}', response, re.DOTALL)
        if match:
            json_str = match.group()
            print(f"json_str: {json_str}")

            message_instance = json.loads(json_str)
            message_instance['session_id'] = session_id
            print(f"message_instance: {message_instance}")
            response_message = Message(**message_instance)
            if "image" in message_instance:
                response_message.image = save_image_from_base64(message_instance['image'])
            return response_message

        else:
            raise ValueError("JSON 형식이 잘못되었습니다.")
    except (json.JSONDecodeError, ValueError) as e:
        print("JSON 디코드 오류:", e)
        print(f"response: {response}")
        return Message(type='message',sender='hero', session_id=session_id, message=response)
    except Exception as e:
        print("예기치 않은 오류 발생:", e)
        print(f"response: {response}")
        return Message(type='message',sender='hero', session_id=session_id, message=response)

def process_messages(messages: List[Dict]) -> str:
    messages = [CustomHumanMessage(
                    content=msg['data']['content'],
                    **msg['data']['additional_kwargs']
                )
                if msg['type'] == "human"
                else CustomAIMessage(
                    content=msg['data']['content'],
                    **msg['data']['additional_kwargs']
                )
                for msg in messages]
    processed_texts = ""
    for msg in messages:
        sender = 'hero' if isinstance(msg, CustomHumanMessage) else 'user'
        processed_text = f"{sender}: {msg.content}\n"
        processed_texts += f'{processed_text}'
    return processed_texts