from rest_framework import generics

from letter_templates.models import LetterTemplate
from letter_templates.serializers import LetterTemplateSerializer


class LetterTemplatesList(generics.ListAPIView):
    """
    Returns list of all letter templates
    """
    queryset = LetterTemplate.objects.all()
    serializer_class = LetterTemplateSerializer


class LetterTemplateDetail(generics.RetrieveAPIView):
    """
    Returns detail of a specific letter template
    """
    queryset = LetterTemplate.objects.all()
    serializer_class = LetterTemplateSerializer
