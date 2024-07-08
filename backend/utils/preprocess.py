from PIL import Image
import base64
import re
import json
import io
from backend.model.message import Message
from backend.utils.vision_util import save_image_from_base64
from typing import Optional
from datetime import datetime
# PIL 이미지 객체 base64 문자열로 변환
def convert_to_base64(image_path, max_size=(256, 256)) -> str:
    with Image.open(image_path) as img:
        img.thumbnail(max_size)
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG")
        return base64.b64encode(buffer.getvalue()).decode('utf-8')

def resize_image(base64_str, size=(256, 256)) -> str:
    # base64 문자열을 바이트로 변환
    image_data = base64.b64decode(base64_str.split(",")[1])

    # 바이트 데이터를 PIL 이미지로 변환
    image = Image.open(io.BytesIO(image_data))

    # 이미지 크기 조정
    resized_image = image.resize(size, Image.LANCZOS)

    # PIL 이미지를 바이트로 변환
    buffered = io.BytesIO()
    resized_image.save(buffered, format="JPEG")
    resized_image_bytes = buffered.getvalue()

    # 바이트 데이터를 base64 문자열로 변환
    resized_base64_str = base64.b64encode(resized_image_bytes).decode('utf-8')

    return resized_base64_str

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
        return None
    except Exception as e:
        print("예기치 않은 오류 발생:", e)
        print(f"response: {response}")
        return None


def read_system_config(filename):
    print(filename)
    with open(filename, 'r', encoding='utf-8') as f:
        return ' '.join(f.readlines())
