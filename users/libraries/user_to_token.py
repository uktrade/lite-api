from users.libraries.token import Token


def user_to_token(user):
    payload = {
        "email": user.email,
        "id": str(user.id),
        "first_name": user.first_name,
        "last_name": user.last_name,
    }
    return Token.encode_json(payload)
