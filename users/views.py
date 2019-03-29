from django.http import JsonResponse
from rest_framework import status

from organisations.models import Organisation
from users.models import User


def users_list(request):
    if request.method == "POST":
        email = request.POST.get('email')
        organisation_id = request.POST.get('organisation_id')
        organisation = Organisation.objects.get(id=organisation_id)

        if request.POST.get('password'):
            password = request.POST.get('password')
        else:
            password = email

        new_user = User(email=email,
                        password=password,
                        organisation=organisation)

        new_user.save()

        return JsonResponse(status=status.HTTP_201_CREATED)
