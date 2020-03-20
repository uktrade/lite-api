import logging
import time
import uuid
from datetime import datetime

from django.db import connection


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

        print(f"\nInitial query count: {len(initial_queries)}")

        response = self.get_response(request)
        final_queries = connection.queries

        elapsed_time = datetime.now() - start

        print(f"Time taken for {request.path}: {round(elapsed_time.microseconds / 100000, 2)}s")
        print(f"Final query count: {len(final_queries)}\n")
        # logging.info(
        #     {
        #         "message": "liteolog db",
        #         "corrID": request.correlation,
        #         "type": "db details",
        #         "elapsed_time": elapsed_time,
        #         "initial query count": len(initial_queries),
        #         "final query count": len(final_queries),
        #         "query set": final_queries,
        #         "method": "DB-QUERY-SET",
        #     }
        # )

        return response
