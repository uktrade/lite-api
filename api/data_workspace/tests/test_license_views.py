import mohawk

from django.conf import settings
from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from urllib import parse

from api.core.requests import get_hawk_sender
from test_helpers.clients import DataTestClient


class DataWorkspaceTests(DataTestClient):
    def setUp(self):
        super().setUp()
        test_host = "http://testserver"
        self.licences = parse.urljoin(test_host, reverse("data_workspace:dw-licences-list"))
        self.ogl_list = parse.urljoin(test_host, reverse("data_workspace:dw-ogl-list"))

    @override_settings(HAWK_AUTHENTICATION_ENABLED=True)
    def test_dw_view_licences(self):
        sender = get_hawk_sender("GET", self.licences, None, settings.HAWK_LITE_DATA_WORKSPACE_CREDENTIALS)
        self.client.credentials(HTTP_HAWK_AUTHENTICATION=sender.request_header, CONTENT_TYPE="application/json")
        response = self.client.get(self.licences)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @override_settings(HAWK_AUTHENTICATION_ENABLED=True)
    def test_dw_view_licences_fail_incorrect_hawk_key(self):
        sender = get_hawk_sender("GET", self.licences, None, "internal-frontend")
        self.client.credentials(HTTP_HAWK_AUTHENTICATION=sender.request_header, CONTENT_TYPE="application/json")
        with self.assertRaises(mohawk.exc.HawkFail):
            self.client.get(self.licences)

    @override_settings(HAWK_AUTHENTICATION_ENABLED=True)
    def test_dw_view_ogl_types(self):
        sender = get_hawk_sender("GET", self.ogl_list, None, settings.HAWK_LITE_DATA_WORKSPACE_CREDENTIALS)
        self.client.credentials(HTTP_HAWK_AUTHENTICATION=sender.request_header, CONTENT_TYPE="application/json")
        response = self.client.get(self.ogl_list)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @override_settings(HAWK_AUTHENTICATION_ENABLED=True)
    def test_dw_view_ogl_fail_incorrect_hawk_key(self):
        sender = get_hawk_sender("GET", self.ogl_list, None, "internal-frontend")
        self.client.credentials(HTTP_HAWK_AUTHENTICATION=sender.request_header, CONTENT_TYPE="application/json")
        with self.assertRaises(mohawk.exc.HawkFail):
            self.client.get(self.ogl_list)
