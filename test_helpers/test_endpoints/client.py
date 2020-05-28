from conf import requests

from conf.settings import env


def get(appended_address, headers):
    url = _build_absolute_uri(appended_address)
    return requests.get(url, headers)


def _build_absolute_uri(appended_address):
    url = env("PERFORMANCE_TEST_HOST") + appended_address.replace(" ", "%20")

    if not url.endswith("/") and "?" not in url:
        url = url + "/"

    return url
