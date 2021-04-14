import logging
from urllib.parse import urljoin

import requests
from requests.exceptions import RequestException
from authbroker_client.utils import get_client
from django.conf import settings
from django.http import StreamingHttpResponse
from rest_framework.exceptions import ValidationError
from mohawk import Receiver
from mohawk.util import prepare_header_val, utc_now


logger = logging.Logger(__name__)

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


class TokenIntrospectionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def introspect(self, request):
        user_token = request.META.get('HTTP_GOV_USER_TOKEN')
        cache_key = f"sso_introspection:{user_token}"
        if (cache.get(cache_key)):
            return
        else:
            cache.set(cache_key, timout=SSO_INTROSPECTION_TTL)
        response = requests.post(
            urljoin(settings.AUTHBROKER_URL, '/o/introspect'),
            data={'token': user_token}
            headers={
                'Authorization': f'Bearer {settings.STAFF_SSO_AUTH_TOKEN}',
                'Accept': 'application/json;q=0.9,*/*;q=0.8'
            },
            timeout=settings.STAFF_SSO_REQUEST_TIMEOUT,
        )
        if not response.json()['active']:
            raise ValidationError()

    def __call__(self, request):
        try:
            self.introspect(request)
        except RequestException:
            raise ValidationError('SSO introspection request failed.')
        return self.get_response(request)
