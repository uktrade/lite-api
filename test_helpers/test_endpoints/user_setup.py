from conf.settings import env

from test_helpers.test_endpoints.client import get, post
from json import loads as serialize


def get_users(env_variable):
    admin_users = env(env_variable)
    # The JSON representation of the variable is different on environments, so it needs to be parsed first
    parsed_admin_users = admin_users.replace("=>", ":")

    try:
        serialized_admin_users = serialize(parsed_admin_users)
    except ValueError:
        raise ValueError(
            f"INTERNAL_ADMIN_TEAM_USERS has incorrect format;"
            f"\nexpected format: [{{'email': '', 'role': ''}}]"
            f"\nbut got: {admin_users}"
        )

    return serialized_admin_users


def login_exporter():
    # TODO: move over to env defined individual user
    exporter_user = {"email": env("PERFORMANCE_EXPORTER_USER")}

    exporter_user = {
        "email": exporter_user["email"],
        "user_profile": {"first_name": "first_name", "last_name": "last_name"},
    }

    response, _ = post(request=None, appended_address="/users/authenticate/", json=exporter_user)
    exporter_user = {
        "email": exporter_user["email"],
        "EXPORTER-USER-TOKEN": response["token"],
        "user_id": response["lite_api_user_id"],
    }

    response = get(request=exporter_user, appended_address=f"/users/me/", is_gov=False)
    # TODO: have ability to select certain org
    # TODO: have ability to choose HMRC/not
    exporter_user["organisation-id"] = response.json()["user"]["organisations"][0]["id"]

    return exporter_user


def login_internal():
    # TODO: move over to env defined individual user
    gov_user = {"email": env("PERFORMANCE_GOV_USER")}
    gov_user["first_name"] = "test"
    gov_user["last_name"] = "er"

    response, _ = post(request=None, appended_address="/gov-users/authenticate/", json=gov_user)
    gov_user = {
        "email": gov_user["email"],
        "GOV-USER-TOKEN": response["token"],
        "user_id": response["lite_api_user_id"],
    }

    return gov_user
