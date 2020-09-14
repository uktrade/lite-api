from django.http import StreamingHttpResponse
from mohawk import Receiver
from mohawk.util import prepare_header_val, utc_now


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
