from django.http import JsonResponse
from rest_framework import generics, status

from conf.authentication import GovAuthentication
from letter_templates.models import LetterTemplate
from letter_templates.serializers import LetterTemplateSerializer


class LetterTemplatesList(generics.ListCreateAPIView):
    """
    Returns list of all letter templates or creates a letter template
    """
    queryset = LetterTemplate.objects.all()
    serializer_class = LetterTemplateSerializer
    authentication_classes = (GovAuthentication,)

    def post(self, request, *args, **kwargs):
        print('\n')
        print(request.data)
        print('\n')
        serializer = self.serializer_class(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return JsonResponse(data=serializer.data, status=status.HTTP_201_CREATED)

        print('\n')
        print(serializer.errors)
        print('\n')

        return JsonResponse(data={'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class LetterTemplateDetail(generics.RetrieveUpdateAPIView):
    """
    Returns detail of a specific letter template
    """
    queryset = LetterTemplate.objects.all()
    serializer_class = LetterTemplateSerializer
    authentication_classes = (GovAuthentication,)

    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)
