from users.libraries.token import Token


def user_to_token(user):
    payload = {
        'email': user.email,
        'id': str(user.id),
        'first_name': user.first_name,
        'last_name': user.last_name
    }
    return Token.encode_json(payload)


def users_to_tokens(users):
    tokens = []
    print(users)
    for user in users:
        print(user.organisation.name)
        tokens.append({'token': user_to_token(user),
                       'organisation': user.organisation.name,
                       'first_name': user.first_name,
                       'last_name': user.last_name,
                       'lite_api_user_id': str(user.id)})
    return tokens
