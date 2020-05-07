import requests

from conf.settings import env
from organisations.libraries.get_organisation import get_request_user_organisation_id


def get(request, appended_address):
    """
    :param request: user headers/meta for the api to look at
    :param appended_address: the end of url which we wish to send request against e.g. "/cases/"
    :return: request response from server
    """
    if request:
        return requests.get(env("PERFORMANCE_TEST_HOST") + appended_address, headers=request,)

    return requests.get(env("PERFORMANCE_TEST_HOST") + appended_address)


def post(request, appended_address, json):
    if request:
        return requests.post(
            env("PERFORMANCE_TEST_HOST") + appended_address,
            json=json,
            headers={
                "EXPORTER-USER-TOKEN": str(request.user.user_token),
                "X-Correlation-Id": str(request.correlation),
                "ORGANISATION-ID": get_request_user_organisation_id(request),
            },
        )
    else:
        data = requests.post(env("PERFORMANCE_TEST_HOST") + appended_address, json=json)
        return data.json(), data.status_code
