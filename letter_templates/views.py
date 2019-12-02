from django.http import JsonResponse
from rest_framework import generics, status

from conf import constants
from conf.authentication import GovAuthentication
from conf.permissions import assert_user_has_permission
from letter_templates.models import LetterTemplate
from letter_templates.serializers import LetterTemplateSerializer


class LetterTemplatesList(generics.ListCreateAPIView):
    """
    Returns list of all letter templates or creates a letter template
    """

    authentication_classes = (GovAuthentication,)
    serializer_class = LetterTemplateSerializer

    def get_queryset(self):
        return LetterTemplate.objects.all()

    def post(self, request, *args, **kwargs):
        assert_user_has_permission(request.user, constants.GovPermissions.CONFIGURE_TEMPLATES)
        serializer = self.serializer_class(data=request.data)

        if serializer.is_valid():
            serializer.save()
            data = serializer.data
            data["restricted_to"] = list(data["restricted_to"])
            return JsonResponse(data=data, status=status.HTTP_201_CREATED)

        return JsonResponse(data={"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class LetterTemplateDetail(generics.RetrieveUpdateAPIView):
    """
    Returns detail of a specific letter template
    """

    authentication_classes = (GovAuthentication,)
    queryset = LetterTemplate.objects.all()
    serializer_class = LetterTemplateSerializer

    def update(self, request, *args, **kwargs):
        assert_user_has_permission(request.user, constants.GovPermissions.CONFIGURE_TEMPLATES)
        serializer = self.get_serializer(self.get_object(), data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return JsonResponse(serializer.data)

        return JsonResponse({"errors": serializer.errors})
