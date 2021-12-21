import json


def register_user(username, password):
    users = {}
    with open('users.json', 'r') as f:
        users = json.loads(f.read())
        if users.get(username):
            return 'User already exists'
        else:
            users[username] = password
            with open('users.json', 'w') as f:
                f.write(json.dumps(users))
            return 'Success'


print(register_user('kirill1', 'turpoxod'))