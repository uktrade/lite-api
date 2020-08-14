from api.conf import requests

from api.conf.settings import env, HAWK_LITE_PERFORMANCE_CREDENTIALS


def get(appended_address, headers=None):
    url = _build_absolute_uri(appended_address).replace(" ", "%20")
    return requests.get(url, headers=headers, hawk_credentials=HAWK_LITE_PERFORMANCE_CREDENTIALS)


def post(appended_address, request_data, headers=None):
    url = _build_absolute_uri(appended_address)
    return requests.post(url, request_data, headers=headers, hawk_credentials=HAWK_LITE_PERFORMANCE_CREDENTIALS)


def _build_absolute_uri(appended_address):
    url = env("PERFORMANCE_TEST_HOST") + appended_address

    if not url.endswith("/") and "?" not in url:
        url = url + "/"

    return url
