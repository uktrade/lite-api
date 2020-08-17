from rest_framework.views import exception_handler


def lite_exception_handler(exc, context):
    # Call REST framework's default exception handler first,
    # to get the standard error response.
    response = exception_handler(exc, context)

    # Add parent "errors"
    if response is not None:
        response.data = {"errors": response.data}

    return response
