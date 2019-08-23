import json
import logging
import uuid
import time


class LoggingMiddleware:
    def __init__(self, get_response=None):
        self.get_response = get_response

    def __call__(self, request):
        correlation = None
        start = time.time()
        if 'HTTP_X_CORRELATION_ID' in request.META:
            correlation = request.META['HTTP_X_CORRELATION_ID']
        request.correlation = correlation or uuid.uuid4().hex
        response = self.get_response(request)
        logging.info({
            "message": "liteolog",
            "corrID": request.correlation,
            "type": "http",
            "method": request.method,
            "url": request.path,
            "elapsed_time": time.time() - start
        })

        return response

