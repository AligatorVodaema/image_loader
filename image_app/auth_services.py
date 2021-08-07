from conf import *
import hashlib
import hmac
import json
from typing import Optional
import base64
from http import cookies




def sign_data(msg: str) -> str:
    '''Подписывает логин пользователя.'''
    return hmac.new(
        SECRET_KEY.encode(),
        msg=msg.encode(),
        digestmod=hashlib.sha256
    ).hexdigest().upper()


def verify_password(raw_json_data: bytes) -> bool:
    """Проверка переданного хэша пароля с хешом в 'типо дб'."""
    user_json_data = json.loads(raw_json_data)
    username = user_json_data['username']
    password = user_json_data['password']

    password_hash = hashlib.sha256((password + 
        PASSWORD_SALT).encode()).hexdigest().lower()
    stored_password_hash = users[username]['password'].lower()
    return password_hash == stored_password_hash


def raw_json_validation(msg: bytes) -> bool:
    """Валидация сырого json и проверка переданного json'a."""
    try:
        json_data = json.loads(msg)
        if json_data['username'] not in users.keys():
            raise KeyError

        if not all((json_data['username'], json_data['password'])):
            raise ValueError
        
    except Exception:
        return False
    return True


def prepare_json_for_response(dict: dict) -> bytes:
        msg = json.dumps(dict)
        return msg.encode()


def get_username_from_signed_string(username_signed: str) -> Optional[str]:
    """Парсинг подписанной строки. Сравнивает username с 
    подписанным username."""
    username_base64, sign = username_signed.split('.')
    username = base64.b64decode(username_base64.encode()).decode()
    valid_sign = sign_data(username)
    if hmac.compare_digest(valid_sign, sign):
        return username


def make_the_cookie(username: str) -> cookies.SimpleCookie:
        """Создаёт куку для залогиненного пользователя."""

        username_signed = base64.b64encode(username.encode()).decode() \
            + '.' + sign_data(username)

        cookie = cookies.SimpleCookie()
        cookie['username'] = username_signed
        return cookie