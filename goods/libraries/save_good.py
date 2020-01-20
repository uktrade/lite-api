from django.http import JsonResponse
from rest_framework import status

from conf.helpers import str_to_bool


def create_or_update_good(serializer, validate_only, success_response_code):
    if not serializer.is_valid():
        errors = serializer.errors
        pv_grading_errors = errors.pop("pv_grading_details", None)
        flattened_errors = {**errors, **pv_grading_errors} if pv_grading_errors else errors
        return JsonResponse(data={"errors": flattened_errors}, status=status.HTTP_400_BAD_REQUEST)

    if str_to_bool(validate_only):
        return JsonResponse(data={"good": serializer.data}, status=status.HTTP_200_OK)

    serializer.save()
    return JsonResponse(data={"good": serializer.data}, status=success_response_code)
