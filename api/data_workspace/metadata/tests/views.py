from rest_framework import viewsets
from rest_framework.response import Response


class FakeTableViewSet(viewsets.ViewSet):
    class DataWorkspace:
        table_name = "fake_table"

    def list(self, request):
        return Response({})

    def retrieve(self, request, pk):
        return Response({})


class AnotherFakeTableViewSet(viewsets.ViewSet):
    class DataWorkspace:
        table_name = "another_fake_table"
        indexes = ["one", "two", "three"]

    def list(self, request):
        return Response({})

    def retrieve(self, request, pk):
        return Response({})
