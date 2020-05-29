from json import dumps as serialize
import logging

import requests
from django.core.cache import cache
from mohawk import Sender
from mohawk.exc import AlreadyProcessed

from conf.settings import HAWK_AUTHENTICATION_ENABLED, HAWK_RECEIVER_NONCE_EXPIRY_SECONDS, HAWK_CREDENTIALS

API_HAWK_CREDENTIALS = "lite-api"


def get(url, headers=None, hawk_credentials=None):
    return make_request("GET", url, headers=headers, hawk_credentials=hawk_credentials)


def post(url, data, headers=None, hawk_credentials=None):
    return make_request("POST", url, data=data, headers=headers, hawk_credentials=hawk_credentials)


def put(url, data, headers=None, hawk_credentials=None):
    return make_request("PUT", url, data=data, headers=headers, hawk_credentials=hawk_credentials)


def make_request(method, url, data=None, headers=None, hawk_credentials=None):
    headers = headers or {}  # If no headers are supplied, default to an empty dictionary
    headers["content-type"] = "application/json"

    if HAWK_AUTHENTICATION_ENABLED:
        sender = _get_hawk_sender(method, url, data, hawk_credentials)
        headers["hawk-authentication"] = sender.request_header

        response = requests.request(method, url, json=data, headers=headers)
        _verify_api_response(sender, response)
    else:
        response = requests.request(method, url, json=data, headers=headers)

    return response


def _get_hawk_sender(method, url, data=None, credentials=None):
    credentials = HAWK_CREDENTIALS.get(credentials or API_HAWK_CREDENTIALS)
    content = serialize(data) if data else data

    return Sender(credentials, url, method, content=content, content_type="application/json", seen_nonce=_seen_nonce)


def _seen_nonce(access_key_id, nonce, timestamp):
    """
    Returns if the passed access_key_id/nonce combination has been used before
    """

    cache_key = f"hawk:{access_key_id}:{nonce}"

    # cache.add only adds key if it isn't present
    seen_cache_key = not cache.add(cache_key, True, timeout=HAWK_RECEIVER_NONCE_EXPIRY_SECONDS)

    if seen_cache_key:
        raise AlreadyProcessed(f"Already seen nonce {nonce}")

    return seen_cache_key


def _verify_api_response(sender, response):
    try:
        sender.accept_response(
            response.headers["server-authorization"],
            content=response.content,
            content_type=response.headers["Content-Type"],
        )
    except Exception as exc:  # noqa
        error_prefix = f"Unable to authenticate response from {response.url}"

        if "server-authorization" not in response.headers:
            logging.error(
                f"{error_prefix}. The 'server_authorization' header was not found - probable HAWK misconfiguration"
            )
        else:
            logging.error(f"{error_prefix}. An unhandled exception was encountered -> {type(exc).__name__}: {exc}")
