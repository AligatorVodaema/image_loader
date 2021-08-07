import ast
from io import BytesIO
from typing import List, Tuple
from PIL import Image
import uuid
from requests_toolbelt.multipart import decoder




def parse_multipart_data(data: bytes, content_type: str) -> List[Tuple, ]:
    """Парсинг multipart data. Возвращает List с tuple(headers image, 
    image bytes) каждого изображения"""

    multipart_data = decoder.MultipartDecoder(content=data, 
        content_type=content_type)

    raw_img_and_headers = []
    for part in multipart_data.parts:
        raw_img_and_headers.append((part.headers, part.content))

    return raw_img_and_headers


def valid_content_type(hdrs: bytes) -> bool:
    """Валидация headers image на предмет не изображения."""

    bytes_headers = hdrs.get('Content-Type'.encode())
    content_type = bytes_headers.decode().split('/')[0]
    if content_type != "image":
        return False
    return True


def parse_content_disposition(hdrs: bytes) -> str:
    """Парсинг content disposition для получения названия
    изображения и его тип."""

    bytes_headers = hdrs.get('Content-Disposition'.encode())
    kw_str = bytes_headers.decode().split(";")[-1].strip().split('=')
    image_name = ast.literal_eval(kw_str[-1])
    return image_name


def make_image(img: bytes, img_name: str) -> None:
    """Создание изображения."""
    stream = BytesIO(img)
    img = Image.open(stream)
    uuid_str = str(uuid.uuid4())
    img.save(f'saved_images/{uuid_str}_{img_name}')
    return None