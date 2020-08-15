from rest_framework import generics

from api.conf.authentication import SharedAuthentication
from api.letter_templates.models import LetterLayout
from api.staticdata.letter_layouts.serializers import LetterLayoutSerializer


class LetterLayoutsList(generics.ListAPIView):
    """
    Returns list of all letter layouts
    """

    authentication_classes = (SharedAuthentication,)

    queryset = LetterLayout.objects.all()
    serializer_class = LetterLayoutSerializer


class LetterLayoutDetail(generics.RetrieveAPIView):
    """
    Returns detail of a specific letter layout
    """

    authentication_classes = (SharedAuthentication,)

    queryset = LetterLayout.objects.all()
    serializer_class = LetterLayoutSerializer
