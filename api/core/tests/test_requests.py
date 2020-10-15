from django.test import override_settings
from unittest import mock

from api.core.requests import get, post, put, delete, make_request, send_request
from test_helpers.clients import DataTestClient


class MockHawkSender:
    def __init__(self, request_header: str):
        self.request_header = request_header


class RequestsTests(DataTestClient):
    def setUp(self):
        super().setUp()

    @mock.patch("api.core.requests.make_request")
    def test_get_calls_make_requests(self, make_request):
        make_request.return_value = None

        get("url", headers=None, hawk_credentials="fake-id", timeout=5)

        make_request.assert_called_with("GET", "url", headers=None, hawk_credentials="fake-id", timeout=5)

    @mock.patch("api.core.requests.make_request")
    def test_post_calls_make_requests(self, make_request):
        make_request.return_value = None

        post("url", {"data": "stuff"}, headers=None, hawk_credentials="fake-id", timeout=5)

        make_request.assert_called_with(
            "POST", "url", data={"data": "stuff"}, headers=None, hawk_credentials="fake-id", timeout=5
        )

    @mock.patch("api.core.requests.make_request")
    def test_put_calls_make_requests(self, make_request):
        make_request.return_value = None

        put("url", {"data": "stuff"}, headers=None, hawk_credentials="fake-id", timeout=5)

        make_request.assert_called_with(
            "PUT", "url", data={"data": "stuff"}, headers=None, hawk_credentials="fake-id", timeout=5
        )

    @mock.patch("api.core.requests.make_request")
    def test_delete_calls_make_requests(self, make_request):
        make_request.return_value = None

        delete("url", headers=None, hawk_credentials="fake-id", timeout=5)

        make_request.assert_called_with("DELETE", "url", headers=None, hawk_credentials="fake-id", timeout=5)

    @override_settings(HAWK_AUTHENTICATION_ENABLED=False)
    @mock.patch("api.core.requests.send_request")
    def test_make_request_calls_send_request(self, send_request):
        send_request.return_value = None

        make_request("POST", "url", data={"data": "stuff"}, headers=None, hawk_credentials="fake-id", timeout=5)

        send_request.assert_called_with(
            "POST", "url", data={"data": "stuff"}, headers={"content-type": "application/json"}, timeout=5
        )

    @override_settings(HAWK_AUTHENTICATION_ENABLED=True)
    @mock.patch("api.core.requests.verify_api_response")
    @mock.patch("api.core.requests.send_request")
    @mock.patch("api.core.requests.get_hawk_sender")
    def test_make_request_calls_send_request_with_hawk(self, get_hawk_sender, send_request, verify_api_response):
        mocked_hawk_sender = MockHawkSender("authentication-header")
        mocked_response = None
        get_hawk_sender.return_value = mocked_hawk_sender
        send_request.return_value = mocked_response
        verify_api_response.return_value = None

        make_request("POST", "url", data={"data": "stuff"}, headers=None, hawk_credentials="fake-id", timeout=5)

        get_hawk_sender.assert_called_with("POST", "url", {"data": "stuff"}, "fake-id")
        send_request.assert_called_with(
            "POST",
            "url",
            data={"data": "stuff"},
            headers={"content-type": "application/json", "hawk-authentication": "authentication-header"},
            timeout=5,
        )
        verify_api_response.assert_called_with(mocked_hawk_sender, mocked_response)

    @mock.patch("api.core.requests.requests.request")
    def test_send_request_calls_requests_library(self, request):
        request.return_value = None

        send_request("POST", "url", data={"data": "stuff"}, headers={"content-type": "application/json"}, timeout=5)

        request.assert_called_with(
            "POST", "url", json={"data": "stuff"}, headers={"content-type": "application/json"}, timeout=5
        )
