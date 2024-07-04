import base64
from PIL import Image, ImageFilter
import io
from typing import Dict
import os
from backend.core.config import settings


def save_image_from_base64(data: str, filename: str = 'img.jpg') -> str:
    # 데이터 URL 형식의 base64 문자열 처리
    if ',' in data:
        header, data = data.split(',', 1)

    # base64 문자열을 바이트로 변환
    data_bytes = base64.b64decode(data)

    # 파일 저장 경로 설정
    root_path = settings.ROOT_DIR
    file_path = os.path.join(root_path, "backend", "datas", filename)

    # 파일 저장
    with open(file_path, 'wb') as f:
        f.write(data_bytes)

    return file_path

def load_image_from_path(path: str) -> bytes:
    content = Image.open(path)
    if content.mode == 'RGBA':
        content = content.convert('RGB')
    sharpened = content.filter(ImageFilter.SHARPEN)
    byte_stream = io.BytesIO()
    sharpened.save(byte_stream, format='JPEG')
    byte_stream.seek(0)
    return byte_stream.read()

def load_image_from_base64(data: str) -> bytes:
    base64_data = data.split(',')[1]
    return base64.b64decode(base64_data)

def web_detection_to_dict(annotations) -> Dict:
    result = {
        'urls': [],
        'images': [],
        'entities': []
    }

    if annotations.pages_with_matching_images:
        result['urls'] = [page.url for page in annotations.pages_with_matching_images]

    if annotations.partial_matching_images:
        result['images'] = [image.url for image in annotations.partial_matching_images]

    if annotations.web_entities:
        result['entities'] = " ".join([f"'description': {entity.description}" for entity in annotations.web_entities[:5]])

    return result
