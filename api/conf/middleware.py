import logging
import time
import uuid

from django.db import connection
from django.http import StreamingHttpResponse
from mohawk import Receiver
from mohawk.util import prepare_header_val, utc_now


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

        # Sign response
        if hasattr(request, "auth") and isinstance(request.auth, Receiver):
            # To handle StreamingHttpResponses such as document downloads
            # we validate the response using the content-disposition (which includes the filename)
            # For all normal HTTPResponses we use the response content.
            if isinstance(response, StreamingHttpResponse):
                signing_content = response["content-disposition"]
            else:
                signing_content = response.content

            # Get mohawk to produce the header for the response
            response_header = request.auth.respond(content=signing_content, content_type=response["Content-Type"])

            # Manually add in the nonce we were called with and the current date/time as timestamp.  The API
            # does not expect clients to validate the nonce, these values are included to workaround an issue
            # in mohawk that meant a nonce checking warning was being unavoidably logged on the client side
            response_header = '{header}, nonce="{nonce}"'.format(
                header=response_header, nonce=prepare_header_val(request.auth.parsed_header["nonce"])
            )
            response_header = '{header}, ts="{nonce}"'.format(
                header=response_header, nonce=prepare_header_val(str(utc_now()))
            )

            response["Server-Authorization"] = response_header

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
