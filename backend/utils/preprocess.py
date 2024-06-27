from PIL import Image
from io import BytesIO
import base64
import re
import json
import io
from backend.model.message import Message
from backend.utils.vision_util import save_image_from_base64
from typing import Optional
# PIL 이미지 객체 base64 문자열로 변환
def convert_to_base64(image_path, max_size=(256, 256)) -> str:
    with Image.open(image_path) as img:
        img.thumbnail(max_size)
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG")
        return base64.b64encode(buffer.getvalue()).decode('utf-8')

def resize_image(image_path, max_size=(256, 256)):
    from PIL import Image
    import io
    import base64

    with Image.open(image_path) as img:
        img.thumbnail(max_size)
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG")
        return base64.b64encode(buffer.getvalue()).decode('utf-8')

def str_to_message(response: str, image: str) -> Optional[Message] or str:
    try:
        print(f"response: {response}")
        # 정규 표현식을 사용하여 중괄호 {} 영역만 추출
        match = re.search(r'\{.*\}', response, re.DOTALL)
        if match:
            json_str = match.group()
            print(f"json_str: {json_str}")

            message_instance = json.loads(json_str)
            print(f"message_instance: {message_instance}")

            response_message = Message(**message_instance)
            if image:
                response_message.image = save_image_from_base64(image)
        else:
            raise ValueError("JSON 형식이 잘못되었습니다.")
    except (json.JSONDecodeError, ValueError) as e:
        print("JSON 디코드 오류:", e)
        print(f"response: {response}")
        return {"error": "유효하지 않은 JSON 형식", "response": response}
    except Exception as e:
        print("예기치 않은 오류 발생:", e)
        print(f"response: {response}")
        return {"error": "예기치 않은 오류 발생", "response": response}
    return response_message


def read_system_config(filename):
    print(filename)
    with open(filename, 'r', encoding='utf-8') as f:
        return ' '.join(f.readlines())