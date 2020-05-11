import json

import requests
from django.contrib.auth.models import AnonymousUser
from mohawk import Sender

from conf.settings import env
from organisations.libraries.get_organisation import get_request_user_organisation_id


def get(request, appended_address):
    url = env("PERFORMANCE_TEST_HOST") + appended_address

    if not url.endswith("/") and "?" not in url:
        url = url + "/"

    if request:
        sender = _get_hawk_sender(url, "GET", "text/plain", {})

        response = requests.get(url, headers=_get_headers(request, sender))

        _verify_api_response(response, sender)

        return response

    return requests.get(url)


def post(request, appended_address, request_data):
    url = env("PERFORMANCE_TEST_HOST") + appended_address
    if not appended_address.endswith("/"):
        url = url + "/"

    if request:
        sender = _get_hawk_sender(url, "POST", "application/json", json.dumps(request_data))

        response = requests.post(url, json=request_data, headers=_get_headers(request, sender))

        _verify_api_response(response, sender)

        return response
    else:
        response = requests.post(env("PERFORMANCE_TEST_HOST") + appended_address, json=json.dumps(request_data))
        return response.json(), response.status_code


def _get_headers(request, sender: Sender):
    headers = {
        "X-Correlation-Id": str(request.correlation),
        "Authorization": sender.request_header,
    }

    if not isinstance(request.user, AnonymousUser):
        headers["EXPORTER-USER-TOKEN"] = str(request.user.user_token)
        headers["ORGANISATION-ID"] = get_request_user_organisation_id(request)

    return headers


def _get_hawk_sender(url, method, content_type, content):
    return Sender(
        credentials={"id": "lite-performance", "key": env("LITE_PERFORMANCE_HAWK_KEY"), "algorithm": "sha256"},
        url=url,
        method=method,
        content=content,
        content_type=content_type,
    )


def _verify_api_response(response, sender: Sender):
    sender.accept_response(
        response_header=response.headers["server-authorization"],
        content=response.content,
        content_type=response.headers["Content-Type"],
    )
