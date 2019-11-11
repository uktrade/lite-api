from rest_framework import generics

from letter_templates.models import LetterLayout
from static.letter_layouts.serializers import LetterLayoutSerializer


class LetterLayoutsList(generics.ListAPIView):
    """
    Returns list of all letter layouts
    """
    queryset = LetterLayout.objects.all()
    serializer_class = LetterLayoutSerializer


class LetterLayoutDetail(generics.RetrieveAPIView):
    """
    Returns detail of a specific letter layout
    """
    queryset = LetterLayout.objects.all()
    serializer_class = LetterLayoutSerializer
