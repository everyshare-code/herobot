import base64
from PIL import Image, ImageFilter
import io
from typing import Dict
import os

def save_image_from_base64(data: str, filename: str='img.jpg') -> str:
    data_bytes = base64.b64decode(data)
    root_path = os.getenv('ROOT_DIR')
    file_path = os.path.join(root_path, "backend", "datas", filename)
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
        result['entities'] = "\n".join([f"score:{entity.score}, 'description': {entity.description}" for entity in annotations.web_entities])

    return result
