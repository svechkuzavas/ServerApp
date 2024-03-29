import json
import os
import socket
import datetime

import config


class HTTPServer:
    def __init__(self, port):
        self._port = port

    def run(self):
        serv_sock = socket.socket(
            socket.AF_INET,
            socket.SOCK_STREAM)
        try:
            serv_sock.bind(('', self._port))
            serv_sock.listen(1)
            print(f"Server is started and listening on port {self._port}")
            while True:
                conn, addr = serv_sock.accept()
                print(f"New connection: {str(addr)}")
                try:
                    self.handle_client(conn)
                except Exception as e:
                    print('Client handling failed', e)
        finally:
            serv_sock.close()

    def handle_client(self, conn):
        try:
            req = self.parse_request(conn)
            self.send_response(conn, req['data'])
        except ConnectionResetError:
            conn = None
        except Exception as e:
            self.send_error(conn, e)
        if conn:
            conn.close()

    def parse_request(self, conn):
        rfile = conn.makefile('r')
        raw = rfile.readline(64*1024 + 1).split()
        data = ''
        print(raw)
        filename = '/register' if raw[1] == '/' else raw[1]
        if '/register' in raw[1].split('?'):
            name, password = raw[1].split('?')[1].split('&')
            name = name.split('=')[1]
            password = password.split('=')[1]
            data = f'<html><head><meta charset="UTF-8"></head><body>' \
                   f'{self.register_user(name, password)}</body></html>'
        else:
            data = self.read_file(filename) if raw[1] != '/close' else 'Server closed'
        return {
            'method': raw[0],
            'route': raw[1],
            'data': data,
        }

    def read_file(self, route):
        with open(os.path.join('static', 'html', f'{route[1:]}.html')) as f:
            return ''.join(f.readlines())

    def send_response(self, conn, resp_body):
        response = f"""HTTP/1.1 200 OK
Server: KirillZaycevWebServer v0.0.1
Content-type: text/html
Connection: keep-alive
Date: {datetime.date.today()}
Content-length: {len(resp_body)}

{resp_body}
"""
        conn.send(response.encode())

    def send_error(self, conn, err):
        print(err)

    def register_user(self, username, password):
        users = {}
        with open('users.json', 'r') as f:
            users = json.loads(f.read())
            if users.get(username):
                return 'User already exists'
            else:
                users[username] = [password, False, -1, -1, False, -1]
                with open('users.json', 'w') as f:
                    f.write(json.dumps(users))
                return 'Success'


if __name__ == '__main__':
    server = HTTPServer(config.A_PORT)
    server.run()