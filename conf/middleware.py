import logging
import time
import uuid
from django.db import connection

from conf.authentication import sign_rendered_response


class LoggingMiddleware:
    def __init__(self, get_response=None):
        self.get_response = get_response

    def __call__(self, request):
        correlation = None
        start = time.time()
        if "HTTP_X_CORRELATION_ID" in request.META:
            correlation = request.META["HTTP_X_CORRELATION_ID"]
        request.correlation = correlation or uuid.uuid4().hex
        response = self.get_response(request)
        logging.info(
            {
                "user": request.user.id if request.user else None,
                "message": "liteolog api",
                "corrID": request.correlation,
                "type": "http response",
                "method": request.method,
                "url": request.path,
                "elapsed_time": time.time() - start,
            }
        )

        return response


class HawkSigningMiddleware:
    def __init__(self, get_response=None):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        response = sign_rendered_response(request, response)

        return response


class DBLoggingMiddleware:
    def __init__(self, get_response=None):
        self.get_response = get_response

    def __call__(self, request):
        start = time.time()
        initial_queries = connection.queries
        response = self.get_response(request)
        final_queries = connection.queries

        elapsed_time = time.time() - start
        logging.info(
            {
                "message": "liteolog db",
                "corrID": request.correlation,
                "type": "db details",
                "elapsed_time": elapsed_time,
                "initial query count": len(initial_queries),
                "final query count": len(final_queries),
                "query set": final_queries,
                "method": "DB-QUERY-SET",
            }
        )

        return response
