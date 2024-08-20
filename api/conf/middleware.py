from django.http import StreamingHttpResponse
from mohawk import Receiver
from mohawk.util import prepare_header_val, utc_now
import logging

logger = logging.getLogger(__name__)


class HawkSigningMiddleware:
    def __init__(self, get_response=None):
        logger.error("HawkSigningMiddleware - init")
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        logger.error("HawkSigningMiddleware - __call__ - Start")
        # Sign response
        if hasattr(request, "auth") and isinstance(request.auth, Receiver):
            # To handle StreamingHttpResponses such as document downloads
            # we validate the response using the content-disposition (which includes the filename)
            # For all normal HTTPResponses we use the response content.
            if isinstance(response, StreamingHttpResponse):
                signing_content = response["content-disposition"]
                logger.error("HawkSigningMiddleware - __call__ - StreamingHttpResponse instance", signing_content)
            else:
                signing_content = response.content
                logger.error("HawkSigningMiddleware - __call__ -  no StreamingHttpResponse instance", signing_content)

            # Get mohawk to produce the header for the response
            response_header = request.auth.respond(content=signing_content, content_type=response["Content-Type"])
            logger.error("HawkSigningMiddleware - __call__ - response_header 1", response_header)
            # Manually add in the nonce we were called with and the current date/time as timestamp.  The API
            # does not expect clients to validate the nonce, these values are included to workaround an issue
            # in mohawk that meant a nonce checking warning was being unavoidably logged on the client side
            response_header = '{header}, nonce="{nonce}"'.format(
                header=response_header, nonce=prepare_header_val(request.auth.parsed_header["nonce"])
            )
            logger.error("HawkSigningMiddleware - __call__ - response_header 2", response_header)
            response_header = '{header}, ts="{nonce}"'.format(
                header=response_header, nonce=prepare_header_val(str(utc_now()))
            )
            logger.error("HawkSigningMiddleware - __call__ - response_header 3", response_header)
            response["Server-Authorization"] = response_header
        logger.error("HawkSigningMiddleware - __call__ - Finish")
        return response
