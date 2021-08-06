from PIL import Image
from io import BytesIO
from http.server import BaseHTTPRequestHandler,HTTPServer
from http import cookies
import json
from conf import *
import hashlib
import hmac
import base64
from requests_toolbelt.multipart import decoder
import ast
import uuid


users = {
    'Peter': {
        'password': '457c79d039a90319af195ed01f9a76e89c64521249ee2af5bea457ca2ee2b683'
        },
    'Vasiliy': {
        'password': 'b9aeec834d3d2aac73f2c86fa6374341526bf746fa101d74491a122e783d976d'
    }
}

def sign_data(welcome_msg: str) -> str:
    '''Возвращает подписанные данные welcome_msg'''
    return hmac.new(
        SECRET_KEY.encode(),
        msg=welcome_msg.encode(),
        digestmod=hashlib.sha256
    ).hexdigest().upper()


def verify_password(raw_json_data):
    user_json_data = json.loads(raw_json_data)
    username = user_json_data['username']
    password = user_json_data['password']

    password_hash = hashlib.sha256((password + PASSWORD_SALT).encode()).hexdigest().lower()
    stored_password_hash = users[username]['password'].lower()
    return password_hash == stored_password_hash

def raw_json_validation(welcome_msg):
    try:
        json_data = json.loads(welcome_msg)
        if json_data['username'] not in users.keys():
            raise KeyError

        if not all((json_data['username'], json_data['password'])):
            raise ValueError
        
    except Exception:
        return False
    return True


def prepare_json_for_response(dict):
        welcome_msg = json.dumps(dict)
        return welcome_msg.encode()


class AuthHandler(BaseHTTPRequestHandler):

    def make_the_cookie(self, username: str) -> cookies.SimpleCookie:
        username_signed = base64.b64encode(username.encode()).decode() \
            + '.' + sign_data(username)

        cookie = cookies.SimpleCookie()
        cookie['username'] = username_signed
        return cookie


    def downland_image(self):
        self.send_response(200)
        


    def do_POST(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        
        # print(self.headers['Content-Type'])

        if self.path == '/api/for_image':
            self.end_headers()
            # print(self.headers['Content-Length'])
            # print(self.headers['Content-Type'])

            print('incoming request is', self.headers['Content-Length'], 'bytes')
            if int(self.headers['Content-Length']) > 200000:
                return self.wfile.write((json.dumps(INVALID_FILE_SIZE)).encode())

            data = self.rfile.read(int(self.headers['Content-Length']))

            multipart_data = decoder.MultipartDecoder(content=data, 
                content_type=self.headers['Content-type'])

            raw_img_and_headers = []
            for part in multipart_data.parts:
                raw_img_and_headers.append((part.headers, part.content))

            # print(raw_img_and_headers)

            # bytes_headers = got_headers.get('Content-Disposition'.encode())
            # kw_str = bytes_headers.decode().split(";")[-1].strip().split('=')
            # image_name = ast.literal_eval(kw_str[-1])

            for hdrs, img in raw_img_and_headers:
                bytes_headers = hdrs.get('Content-Disposition'.encode())
                kw_str = bytes_headers.decode().split(";")[-1].strip().split('=')
                image_name = ast.literal_eval(kw_str[-1])

                stream = BytesIO(img)
                img = Image.open(stream)
                uuid_str = str(uuid.uuid4())
                img.save(f'saved_images/{uuid_str}_{image_name}')
            
            """{b'Content-Disposition': b'form-data; name=""; filename="111.png"', 
            b'Content-Type': b'image/png'}"""

            return self.wfile.write((json.dumps({'msg':'success'})).encode())


        if self.headers['Content-Type'] != 'application/json' \
            or self.path != '/auth':
            error_message = prepare_json_for_response(NOT_IMPLEMENTED)
            return self.wfile.write(bytes(error_message))

        raw_json_data = self.rfile.read(int(self.headers['Content-Length']))

        if not raw_json_validation(raw_json_data) or not verify_password(raw_json_data):
            return self.wfile.write(prepare_json_for_response(NO_VALID_DATA))

        user_json_data = json.loads(raw_json_data)
        username = user_json_data['username']

        print(user_json_data)

        cookie = self.make_the_cookie(username=username)
        self.send_header('Set-Cookie', cookie.output(header=''))
        self.end_headers()

        # print(self.__dict__)
        # print(self.__dict__.keys())


        welcome_msg = json.dumps({'message': f'Hello {username}'})
        return self.wfile.write(bytes(welcome_msg.encode()))
    

    


            
if __name__ == '__main__':


    httpd = HTTPServer(("127.0.0.1", 8000), AuthHandler)
    httpd.serve_forever()
