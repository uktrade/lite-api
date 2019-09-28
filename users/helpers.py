from django.http.response import JsonResponse

from rest_framework import status


def bad_request_if_user_edit_own_status(request, data, user):
    if 'status' in data.keys():
        if user.id == request.user.id:
            return JsonResponse(data={'errors': 'A user cannot change their own status'},
                                status=status.HTTP_400_BAD_REQUEST)

def unassign_from_cases(_, __, user):
    user.unassign_from_cases()
