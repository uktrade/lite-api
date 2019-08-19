import json
import logging
import uuid
from django.utils.deprecation import MiddlewareMixin


class LoggingMiddleware(MiddlewareMixin):

    @staticmethod
    def process_request(self, request):
        request.correlation = uuid.uuid4().hex
        logging.info(json.dumps({
            "correlation": request.correlation,
            "type": "request",
            "path": request.path,
            "method": request.method,
        }))

    @staticmethod
    def process_response(self, request, response):
        logging.info(json.dumps({
            "correlation": request.correlation,
            'type': 'response',
            "status": response.status_code,
        }))
        return response
