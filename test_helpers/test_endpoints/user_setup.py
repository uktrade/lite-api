from conf.settings import env

from test_helpers.test_endpoints.client import get, post
from json import loads as serialize


def get_users(env_variable):
    user = env(env_variable)
    # The JSON representation of the variable is different on environments, so it needs to be parsed first
    parsed_user = user.replace("=>", ":")

    try:
        serialized_user = serialize(parsed_user)
    except ValueError:
        raise ValueError(f"{parsed_user} is an an acceptable value")

    return serialized_user


def login_exporter():
    exporter_user = {
        "email": env("PERFORMANCE_EXPORTER_USER"),
        "user_profile": {"first_name": "first_name", "last_name": "last_name"},
    }

    response, _ = post(request=None, appended_address="/users/authenticate/", json=exporter_user)
    exporter_user = {
        "email": exporter_user["email"],
        "EXPORTER-USER-TOKEN": response["token"],
        "user_id": response["lite_api_user_id"],
        "ORGANISATION-ID": "None",
    }

    response = get(request=exporter_user, appended_address=f"/users/me/")
    organisation_name = env("PERFORMANCE_EXPORTER_ORGANISATION")
    if organisation_name:
        for organisation in response.json()["organisations"]:
            if organisation["name"] == organisation_name:
                exporter_user["ORGANISATION-ID"] = organisation["id"]
                break

        if exporter_user["ORGANISATION-ID"] == "None":
            AttributeError("organisation with that name was not found")

    else:
        # if no organisation name is defined, the first organisation is selected
        exporter_user["ORGANISATION-ID"] = response.json()["organisations"][0]["id"]

    return exporter_user


def login_internal():
    gov_user = {"email": env("PERFORMANCE_GOV_USER"), "first_name": "test", "last_name": "er"}

    response, _ = post(request=None, appended_address="/gov-users/authenticate/", json=gov_user)
    gov_user = {
        "email": gov_user["email"],
        "GOV-USER-TOKEN": response["token"],
        "user_id": response["lite_api_user_id"],
    }

    return gov_user
