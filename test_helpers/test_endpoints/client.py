import json

import requests
from mohawk import Sender

from conf.settings import env, HAWK_AUTHENTICATION_ENABLED


def get(appended_address, headers):
    url = _build_absolute_uri(appended_address.replace(" ", "%20"))

    if HAWK_AUTHENTICATION_ENABLED:
        sender = _get_hawk_sender(url, "GET", "application/json", "")

        headers["hawk-authentication"] = sender.request_header
        headers["content-type"] = sender.req_resource.content_type
        response = requests.get(url, headers=headers)

        _verify_api_response(response, sender)
    else:
        headers["content-type"] = "application/json"
        response = requests.get(url, headers=headers)

    return response


def post(appended_address, headers, request_data):
    url = _build_absolute_uri(appended_address)

    if HAWK_AUTHENTICATION_ENABLED:
        sender = _get_hawk_sender(url, "POST", "application/json", json.dumps(request_data))

        headers["hawk-authentication"] = sender.request_header
        headers["content-type"] = sender.req_resource.content_type
        response = requests.post(url, headers=headers, json=request_data)

        _verify_api_response(response, sender)
    else:
        headers["content-type"] = "application/json"
        response = requests.post(url, headers=headers, json=request_data)

    return response


def _build_absolute_uri(appended_address):
    url = env("PERFORMANCE_TEST_HOST") + appended_address

    if not url.endswith("/") and "?" not in url:
        url = url + "/"

    return url


def _get_hawk_sender(url, method, content_type, content):
    """
    Returns a sender that, for test purposes, is hardcoded to always say that nonces have not been seen before and are
    fine (i.e. with an anonymous check nonce function always returns False)
    """
    return Sender(
        credentials={"id": "lite-performance", "key": env("LITE_PERFORMANCE_HAWK_KEY"), "algorithm": "sha256"},
        url=url,
        method=method,
        content_type=content_type,
        content=content,
        seen_nonce=lambda x, y, z: False,
    )


def _verify_api_response(response, sender):
    try:
        sender.accept_response(
            response.headers["server-authorization"],
            content=response.content,
            content_type=response.headers["Content-Type"],
        )
    except Exception as exc:  # noqa
        if "server-authorization" not in response.headers:
            print(
                "No server_authorization header found in response from the LITE API" " - probable API HAWK auth failure"
            )
        else:
            print(f"Unhandled exception {type(exc).__name__}: {exc}")
        print("We were unable to authenticate your client")
