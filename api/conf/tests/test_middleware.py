import logging
from unittest.mock import MagicMock

from django.http import (
    HttpResponseBadRequest,
    JsonResponse,
)

from rest_framework.response import Response

from api.conf.middleware import BadRequestDebugMiddleware

from django.test import RequestFactory, TestCase


class BadRequestDebugMiddlewareTests(TestCase):
    def test_bad_request_debug_middleware_http_response(self):
        response = HttpResponseBadRequest("Not OK")
        get_response = MagicMock()
        get_response.return_value = response

        with self.assertLogs("api.conf.middleware", level=logging.DEBUG) as cm:
            middleware = BadRequestDebugMiddleware(get_response)
            request_factory = RequestFactory()
            request = request_factory.get("/")
            middleware_response = middleware(request)

        self.assertEqual(response, middleware_response)
        self.assertEqual(cm.output, ["DEBUG:api.conf.middleware:b'Not OK'"])

    def test_bad_request_debug_middleware_json_response(self):
        response = JsonResponse(data={"error": "An error"}, status=400)
        get_response = MagicMock()
        get_response.return_value = response

        with self.assertLogs("api.conf.middleware", level=logging.DEBUG) as cm:
            middleware = BadRequestDebugMiddleware(get_response)
            request_factory = RequestFactory()
            request = request_factory.get("/")
            middleware_response = middleware(request)

        self.assertEqual(response, middleware_response)
        self.assertEqual(cm.output, ['DEBUG:api.conf.middleware:b\'{"error": "An error"}\''])

    def test_bad_request_debug_middleware_drf_response(self):
        response = Response(data={"error": "An error"}, status=400)
        get_response = MagicMock()
        get_response.return_value = response

        with self.assertLogs("api.conf.middleware", level=logging.DEBUG) as cm:
            middleware = BadRequestDebugMiddleware(get_response)
            request_factory = RequestFactory()
            request = request_factory.get("/")
            middleware_response = middleware(request)

        self.assertEqual(response, middleware_response)
        self.assertEqual(cm.output, ["DEBUG:api.conf.middleware:{'error': 'An error'}"])
