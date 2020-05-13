import json

import requests
from mohawk import Sender

from conf.settings import env


def get(appended_address, headers):
    url = _build_absolute_uri(appended_address.replace(" ", "%20"))

    sender = _get_hawk_sender(url, "GET", "application/json", None)

    headers["Authorization"] = sender.request_header
    headers["content-type"] = sender.req_resource.content_type
    response = requests.get(url, headers=headers)

    _verify_api_response(response, sender)

    return response


def post(appended_address, headers, request_data):
    url = _build_absolute_uri(appended_address)

    sender = _get_hawk_sender(url, "POST", "application/json", json.dumps(request_data))

    headers["Authorization"] = sender.request_header
    headers["content-type"] = sender.req_resource.content_type
    response = requests.post(url, headers=headers, json=request_data)

    _verify_api_response(response, sender)

    return response


def _build_absolute_uri(appended_address):
    url = env("PERFORMANCE_TEST_HOST") + appended_address

    if not url.endswith("/") and "?" not in url:
        url = url + "/"

    return url


def _get_hawk_sender(url, method, content_type, content):
    return Sender(
        credentials={"id": "lite-performance", "key": env("LITE_PERFORMANCE_HAWK_KEY"), "algorithm": "sha256"},
        url=url.replace("https", "http"),
        method=method,
        content_type=content_type,
        content=content,
    )


def _verify_api_response(response, sender: Sender):
    sender.accept_response(
        response_header=response.headers["server-authorization"],
        content=response.content,
        content_type=response.headers["Content-Type"],
    )
