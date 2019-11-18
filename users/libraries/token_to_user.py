from users.libraries.token import Token


def token_to_user_pk(token):
    print(token)
    data = Token.decode_to_json(token)
    return data.get("id")
