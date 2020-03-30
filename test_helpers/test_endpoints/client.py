import requests

from conf.settings import env


def get(request, appended_address, is_gov):
    """
    :param request: user headers/meta for the api to look at
    :param appended_address: the end of url which we wish to send request against e.g. "/cases/"
    :param is_gov: boolean field for if a request is being made by gov user or exporter user
    :return: request response from server
    """
    if request:
        if is_gov:
            headers = request
        else:
            headers = {
                "EXPORTER-USER-TOKEN": str(request["EXPORTER-USER-TOKEN"]),
                "ORGANISATION-ID": request.get("organisation-id", "None"),
            }

        return requests.get(env("PERFORMANCE_TEST_HOST") + appended_address, headers=headers,)

    return requests.get(env("PERFORMANCE_TEST_HOST") + appended_address)


def post(request, appended_address, json):
    if request:
        return requests.post(
            env("PERFORMANCE_TEST_HOST") + appended_address,
            json=json,
            headers={
                "EXPORTER-USER-TOKEN": str(request.user.user_token),
                "X-Correlation-Id": str(request.correlation),
                "ORGANISATION-ID": str(request.user.organisation),
            },
        )
    else:
        data = requests.post(env("PERFORMANCE_TEST_HOST") + appended_address, json=json)
        return data.json(), data.status_code
