from django.utils.deprecation import MiddlewareMixin
import logging
import uuid

class LoggingMiddleware(MiddlewareMixin):

    def process_request(self, request):
        # request._correlation = uuid.UUID()
        request.META
        logging.info( "** request **")

    def process_response(self, request, response):
        logging.info( "** response **")
        return response