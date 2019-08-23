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
        logging.info(json.dumps({
            "correlation": request.correlation,
            "type": "request",
            "method": request.method,
            "path": request.path,
        }))
        response = self.get_response(request)
        elapsed = time.time() - start
        logging.info(json.dumps({
            "correlation": request.correlation,
            'type': 'response',
            "status": response.status_code,
            "elapsed": elapsed
        }))
        return response

