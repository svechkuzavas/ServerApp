import json
import random
import socket
import threading
from threading import *

import config

max = 100
list_thread = []
list_conn = []


def logging(*data):
    data = ' '.join((str(item) for item in data))
    with threading.Lock():
        print(data)
        with open("log.txt", 'a+') as file:
            file.write(data + '\n')


class ClientSock(Thread):

    def __init__(self, name, connector, addr):
        Thread.__init__(self)
        self.name = name
        self.connector = connector
        self.addr = addr

    def n(self):
        return self.name

    def run(self):
        self.connector.send("Введите ваш логин: ".encode())
        data = self.connector.recv(1024)
        if data.decode().startswith('telegram'):
            list_conn.append(self.connector)
            userinfo, message = data.decode().split('/')
            self.username = userinfo.split('.')[1]
            broadcast(self.connector, f"[ telegram {self.username} ]: {message}")
            logging(f"[ telegram {self.username} ]: {message}")
            while True:
                data = self.connector.recv(1024)
                userinfo, message = data.decode().split('/')
                username = userinfo.split('.')[1]
                broadcast(self.connector, f"[ telegram {username} ]: {message}")
                logging(f"[ telegram {self.username} ]: {message}")
        else:
            logging(f"[{self.addr[0]}:{self.addr[1]}]: {data.decode()}")
            self.username = data.decode()
            registration = self.check_registered(self.username)
            if registration == config.EXISTS_NOT_CONFIRMED:
                self.connector.send("Пользователь найден. Введите пин с сайта С: ".encode())
                generated_pin = self.generate_pin(self.username)
                input_pin = self.connector.recv(1024).decode()
                logging(f"[ {self.username} ({self.addr[0]}:{self.addr[1]})]: {input_pin}")
                if str(input_pin) == str(generated_pin):
                    self.connector.send("Ок. Вы авторизованы\n".encode())
                    self.confirm_pin(self.username)
                    list_conn.append(self.connector)
                    self.messaging()
                else:
                    self.connector.send("Неправильный пин\n".encode())
            elif registration == config.EXISTS_CONFIRMED:
                self.connector.send("Пользователь найден. Пин подтвержден ранее\n".encode())
                list_conn.append(self.connector)
                self.messaging()
            elif registration == config.NOT_EXISTS:
                self.connector.send("Пользователь не найден. Используйте А для регистрации\n".encode())
                self.run()

    def messaging(self):
        while True:
            data = self.connector.recv(1024).decode()
            if not data:
                break
            broadcast(self.connector, f"[ {self.username} ({self.addr[0]}:{self.addr[1]})]: {data}")
            logging(f"[ {self.username} ({self.addr[0]}:{self.addr[1]})]: {data}")

    def check_registered(self, name):
        with open('users.json', 'r') as f:
            users = json.loads(f.read())
            if users.get(name):
                if users.get(name)[1]:
                    return config.EXISTS_CONFIRMED
                else:
                    return config.EXISTS_NOT_CONFIRMED
            else:
                return config.NOT_EXISTS

    def confirm_pin(self, name):
        with open('users.json', 'r') as f:
            users = json.loads(f.read())
            users.get(name)[1] = True
            with open('users.json', 'w') as f:
                f.write(json.dumps(users))

    def generate_pin(self, username):
        pin = random.randint(1000, 9999)
        with open('static/html/pin.html', 'w') as f:
            f.write(f"""{username}: {pin}""")
        return pin


def broadcast(conn_author, message):
    for client in list_conn:
        if client != conn_author:
            client.send(f"{message}".encode())


sock = socket.socket()
sock.bind(('', config.ECHO_PORT))
sock.listen(4)

while True:
    conn, addr = sock.accept()
    logging(f"New client: {addr[0]}:{addr[1]}")
    thread = ClientSock(len(list_thread), conn, addr)
    list_thread.append(thread if len(list_thread) <= max else Exception)
    thread.start()