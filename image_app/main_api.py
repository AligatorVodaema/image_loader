from http.server import BaseHTTPRequestHandler, HTTPServer
import json
from conf import *
from download_services import *
from auth_services import *




class AuthHandler(BaseHTTPRequestHandler):

    def download_images(self):
        """Загрузка Изображения. Возвращает json(success) 
        если изображение/я загружены."""

        print('incoming request is', self.headers['Content-Length'], 'bytes')

        if int(self.headers['Content-Length']) > 200000:
            return self.wfile.write((json.dumps(INVALID_FILE_SIZE)).encode())
            

        data = self.rfile.read(int(self.headers['Content-Length']))

        raw_img_and_headers = parse_multipart_data(data=data, 
            content_type=self.headers['Content-type'])

        # print(raw_img_and_headers[0][0])

        for hdrs, img in raw_img_and_headers:
            if not valid_content_type(hdrs=hdrs):
                continue
            image_name = parse_content_disposition(hdrs=hdrs)
            make_image(img=img, img_name=image_name)
        
        return self.wfile.write((json.dumps({'msg':'success'})).encode())   


    def authenticate_user(self):
        """Аунтификация пользователя. Валидация 'Content-Type', принятого json'a,
        пароля. Выдача Cookie пользователю."""

        if self.headers['Content-Type'] != 'application/json':
            
            error_message = prepare_json_for_response(NOT_IMPLEMENTED)
            self.wfile.write(bytes(error_message))
            return self.connection.close()

        raw_json_data = self.rfile.read(int(self.headers['Content-Length']))

        if not raw_json_validation(raw_json_data) or not \
            verify_password(raw_json_data):
            self.wfile.write(prepare_json_for_response(NO_VALID_DATA))
            return self.connection.close()

        user_json_data = json.loads(raw_json_data)
        username = user_json_data['username']

        cookie = make_the_cookie(username=username)
        self.send_header('Set-Cookie', cookie.output(header=''))
        self.end_headers()

        welcome_msg = json.dumps({'message': f'Hello {username} !'})
        return self.wfile.write(bytes(welcome_msg.encode()))


    def authorize_user(self):
        """Авторизация пользовотеля. Проверка подписанной cookie установленной
        при Аунтификации."""
        self.end_headers()

        cookie = self.headers['Cookie']
        try:
            username_val = cookie.split(r'"')[1]
        except AttributeError:
            self.wfile.write((json.dumps(NOT_AUTHENTICATED).encode()))
            return self.connection.close()

        clean_username = get_username_from_signed_string(username_val)

        if not cookie or not cookie.startswith('username') or not clean_username:
            self.wfile.write((json.dumps(NOT_AUTHENTICATED).encode()))
            return self.connection.close()

        try:
            user = users[clean_username]
        except KeyError:
            self.wfile.write((json.dumps(NOT_AUTHENTICATED).encode()))
            return self.connection.close()
        return True



    def do_POST(self):
        """Маршрутизация"""

        self.send_response(200)
        self.send_header('Content-type', 'application/json')

        if self.path == '/api/for_image':
            if self.authorize_user():
                self.download_images()

        elif self.path == '/api/auth':
            self.authenticate_user()

        else:
            self.send_response(404)
            self.end_headers()
            return None

            
    
            
if __name__ == '__main__':

    httpd = HTTPServer((IP_FOR_SERVING, PORT_FOR_SERVING), AuthHandler)
    httpd.serve_forever()
