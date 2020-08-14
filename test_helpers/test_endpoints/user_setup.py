from api.conf.settings import env

from test_helpers.test_endpoints.client import get, post


def login_exporter():
    exporter_user = {
        "email": env("PERFORMANCE_EXPORTER_USER"),
        "user_profile": {"first_name": "first_name", "last_name": "last_name"},
    }

    response = post(appended_address="/users/authenticate/", request_data=exporter_user).json()

    exporter_user = {
        "email": exporter_user["email"],
        "EXPORTER-USER-TOKEN": response["token"],
        "user_id": response["lite_api_user_id"],
        "ORGANISATION-ID": "None",
    }

    response = get(appended_address="/users/me/", headers=exporter_user)

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

    response = post(appended_address="/gov-users/authenticate/", request_data=gov_user).json()

    gov_user = {
        "email": gov_user["email"],
        "GOV-USER-TOKEN": response["token"],
        "user_id": response["lite_api_user_id"],
    }

    return gov_user
