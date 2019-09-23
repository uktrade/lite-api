from django.http import JsonResponse
from rest_framework.views import APIView

from static.letter_templates.helpers import get_letter_template
from static.letter_templates.models import LetterTemplate
from static.letter_templates.serializers import LetterTemplateSerializer


class LetterTemplatesList(APIView):
    def get(self, request):
        letter_templates = LetterTemplate.objects.all()
        serializer = LetterTemplateSerializer(letter_templates, many=True)
        return JsonResponse(data={'letter_templates': serializer.data})


class LetterTemplatesDetail(APIView):
    def get(self, request, pk):
        letter_template = get_letter_template(pk)
        serializer = LetterTemplateSerializer(letter_template)
        return JsonResponse(data={'letter_template': serializer.data})
