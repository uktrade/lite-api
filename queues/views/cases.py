from rest_framework import generics

from cases.models import Case
from cases.serializers import SimpleTestSerializer
from conf.pagination import MaxPageNumberPagination


class CasesList(generics.ListAPIView):
    queryset = Case.objects.all()
    serializer_class = SimpleTestSerializer
    pagination_class = MaxPageNumberPagination
