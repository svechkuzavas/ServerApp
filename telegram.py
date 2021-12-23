import json
import random
import socket
import threading

import telebot

import config

bot = telebot.TeleBot(config.TOKEN)
sock = socket.socket()
sock.connect(('localhost', config.ECHO_PORT))
sock.send("telegram.bot/connected".encode())

@bot.message_handler(commands=['login'])
def login(message):
    bot.send_message(message.chat.id, 'Проверяем пользователя в базе')
    username = message.text.split(' ')[1]
    login_state = check_login( username, message.from_user.id )
    if login_state == config.NOT_EXISTS:
        bot.send_message(message.chat.id, 'Такого пользователя не существует. Зарегистрируйтесь на сайте А')
    elif login_state == config.EXISTS_CONFIRMED:
        bot.send_message(message.chat.id, 'Пользователь найден. Пин подтвержден. Можете общаться')
    elif login_state == config.EXISTS_NOT_CONFIRMED:
        generate_pin(username)
        bot.send_message(message.chat.id, 'Пользователь найден. Необходимо ввести ПИН с сайта C')
    elif login_state == config.EXISTS_ALREADY_BINDED:
        bot.send_message(message.chat.id, 'Данный пользователь уже залогинился из другого телеграмм-аккаунта')


@bot.message_handler(commands=['pin'])
def confirm_pin(message):
    username, userdata = read_userdata(message.from_user.id)
    input_pin = message.text.split(' ')[1]
    if userdata is not None:
        if str(userdata[3]) == str(input_pin):
            validate_user(username, message.chat.id)
            bot.send_message(message.chat.id, 'Пин успешно подтвержден. Общайтесь')
        else:
            bot.send_message(message.chat.id, 'Пин неправильный. Повторите команду с правильным кодом')
    else:
        bot.send_message(message.chat.id, 'Пин не был запрошен. Попробуйте снова команду login')


@bot.message_handler(commands=['logout'])
def logout(message):
    username, userdata = None, None
    try:
        username, userdata = read_userdata(message.from_user.id)
    except Exception as e:
        print(e)
    if userdata is not None:
        with open('users.json', 'r') as f:
            users = json.loads(f.read())
            users.get(username)[2] = -1
            users.get(username)[4] = False
            with open('users.json', 'w') as f:
                f.write(json.dumps(users))
        bot.send_message(message.chat.id, 'Вы успешно разлогинились')


@bot.message_handler()
def default_message(message):
    username, userdata = None, None
    try:
        username, userdata = read_userdata(message.from_user.id)
    except Exception as e:
        print(e)
    if userdata is not None:
        if userdata[4]:
            print(f"telegram.{username}/{message.text}")
            sock.send(f"telegram.{username}/{message.text}".encode())
        else:
            bot.send_message(message.chat.id, "Вы не подтвердили пин")
    else:
        bot.send_message(message.chat.id, "Вы не авторизованы")


def validate_user(username, chat_id):
    with open('users.json', 'r') as f:
        users = json.loads(f.read())
        users[username][4] = True
        users[username][5] = chat_id
        with open('users.json', 'w') as f:
            f.write(json.dumps(users))


def check_login(username, tg_id):
    with open('users.json', 'r') as f:
        users = json.loads(f.read())
        if users.get(username):
            if users.get(username)[4] and (str(users.get(username)[2]) == str(tg_id) or str(users.get(username)[2]) == '-1'):
                users.get(username)[2] = tg_id
                with open('users.json', 'w') as f:
                    f.write(json.dumps(users))
                return config.EXISTS_CONFIRMED
            elif not users.get(username)[4] and (str(users.get(username)[2]) == str(tg_id) or str(users.get(username)[2]) == '-1'):
                users.get(username)[2] = tg_id
                with open('users.json', 'w') as f:
                    f.write(json.dumps(users))
                return config.EXISTS_NOT_CONFIRMED
            else:
                return config.EXISTS_ALREADY_BINDED
        else:
            return config.NOT_EXISTS


def generate_pin(username):
    pin = random.randint(1000, 9999)
    with open('static/html/pin.html', 'w') as f:
        f.write(f"""{username}: {pin}""")
    with open('users.json', 'r') as f:
        users = json.loads(f.read())
        if users.get(username):
            users.get(username)[3] = pin
        with open('users.json', 'w') as f:
            f.write(json.dumps(users))
    return pin


def read_userdata(tg_id):
    with open('users.json', 'r') as f:
        users = json.loads(f.read())
        for username, data in users.items():
            if str(data[2]) == str(tg_id):
                return username, data
    return None


def get_chat_ids():
    ids = []
    with open('users.json', 'r') as f:
        users = json.loads(f.read())
        for username, data in users.items():
            if data[5] != -1:
                ids.append(data[5])
    return ids


def receiving():
    while True:
        data = sock.recv(1024)
        if data.decode() != "Введите ваш логин: ":
            with threading.Lock():
                for id in get_chat_ids():
                    bot.send_message(id, data.decode())


if __name__ == '__main__':
    threading.Thread(target=receiving, daemon=True).start()
    bot.polling()