from PIL import Image
from io import BytesIO
import base64
import re
import json
from backend.model.message import Message
# PIL 이미지 객체 base64 문자열로 변환
def convert_to_base64(pil_image: Image) -> str:
    if pil_image is None or not isinstance(pil_image, Image.Image):
        return None
    buffered = BytesIO()
    pil_image.save(buffered, format="JPEG")
    img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
    return img_str

def str_to_message(response: str) -> Message:
    try:
        # 정규 표현식을 사용하여 중괄호 {} 영역만 추출
        start = response.index("{")
        end = response.rindex("}")
        # json_match = re.search(r'\{.*\}', response, re.DOTALL)
        json_str = response[start:end+1]
        if json_str:
            message_instance = json.loads(json_str)
            print(f"message_instance: {message_instance}")
            response_message = Message(**message_instance)
        else:
            raise ValueError("JSON 형식이 잘못되었습니다.")
    except (json.JSONDecodeError, ValueError) as e:
        print("JSON 디코드 오류:", e)
        return {"error": "유효하지 않은 JSON 형식", "response": response}
    return response_message

def read_system_config(filename):
    print(filename)
    with open(filename, 'r', encoding='utf-8') as f:
        return ' '.join(f.readlines())