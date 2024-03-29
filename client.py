import socket
import threading

import config

sock = socket.socket()

sock.connect(('localhost', config.ECHO_PORT))


def receiving():
    while True:
        data = sock.recv(1024)
        with threading.Lock():
            print(data.decode())


threading.Thread(target=receiving, daemon=True).start()
msg = ''
while True:
    if msg == 'exit':
        break
    msg = input()
    sock.send(msg.encode())
