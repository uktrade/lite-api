from django.http import JsonResponse
from rest_framework.views import APIView

from static.letter_templates.models import LetterTemplate
from static.letter_templates.serializers import LetterTemplateSerializer


class LetterTemplatesList(APIView):
    def get(self, request):
        letter_templates = LetterTemplate.objects.all()
        serializer = LetterTemplateSerializer(letter_templates, many=True)
        return JsonResponse(data={'letter_templates': serializer.data})
