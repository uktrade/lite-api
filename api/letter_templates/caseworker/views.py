from api.letter_templates.caseworker.filters import LetterTemplateFilter
from rest_framework.generics import ListAPIView

from api.core.authentication import GovAuthentication
from api.letter_templates.models import LetterTemplate
from .serializers import LetterTemplatesSerializer
from django_filters.rest_framework import DjangoFilterBackend


class LetterTemplatesList(ListAPIView):
    authentication_classes = (GovAuthentication,)
    filter_backends = [DjangoFilterBackend]
    filterset_class = LetterTemplateFilter
    serializer_class = LetterTemplatesSerializer
    queryset = LetterTemplate.objects.order_by("name")
    pagination_class = None
