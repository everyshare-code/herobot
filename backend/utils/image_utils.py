from PIL import Image
import base64
import io

def convert_to_base64(image_path, max_size=(256, 256)) -> str:
    with Image.open(image_path) as img:
        img.thumbnail(max_size)
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG")
        return base64.b64encode(buffer.getvalue()).decode('utf-8')

def resize_image(base64_str, size=(256, 256)) -> str:
    image_data = base64.b64decode(base64_str.split(",")[1])
    image = Image.open(io.BytesIO(image_data))
    resized_image = image.resize(size, Image.LANCZOS)
    buffered = io.BytesIO()
    resized_image.save(buffered, format="JPEG")
    resized_base64_str = base64.b64encode(buffered.getvalue()).decode('utf-8')
    return resized_base64_str
