import logging
import time
import uuid
from datetime import datetime

from django.db import connection

from conf.settings import env
from test_helpers.colours import bold


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

        if not env("SHOW_VIEW_QUERIES"):
            logging.info(
                {
                    "message": "liteolog api",
                    "corrID": request.correlation,
                    "type": "http response",
                    "method": request.method,
                    "url": request.path,
                    "elapsed_time": time.time() - start,
                }
            )

        return response


class DBLoggingMiddleware:
    def __init__(self, get_response=None):
        self.get_response = get_response

    def __call__(self, request):
        start = datetime.now()
        initial_queries = connection.queries

        response = self.get_response(request)
        final_queries = connection.queries

        elapsed_time = datetime.now() - start

        _type = request.method.upper()
        duration = round(elapsed_time.microseconds / 100000, 2)  # noqa
        queries = len(final_queries)

        if env("SHOW_VIEW_QUERIES"):
            print(f"\n{_type} {bold(request.path)} - ⏱  {duration}s  🗂  {queries} queries\n")
        else:
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
