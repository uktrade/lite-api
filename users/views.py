from django.http import JsonResponse
from rest_framework import status, permissions
from rest_framework.decorators import permission_classes

from organisations.models import Organisation
from rest_framework.views import APIView
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


@permission_classes((permissions.AllowAny,))
class UserLogin(APIView):
    def get(self, request):
        email = request.GET.get('email')
        try:
            User.objects.get(email=email)
            return JsonResponse(status=status.HTTP_200_OK, data=email, safe=False)
        except User.DoesNotExist:
            return JsonResponse(status=status.HTTP_401_UNAUTHORIZED, data={'errors': 'Can\'t find user'}, safe=False)