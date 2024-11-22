from rest_framework import viewsets
from rest_framework.response import Response

from . import serializers


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
        fields = [{"name": "id", "primary_key": True, "type": "UUID"}]

    def list(self, request):
        return Response({})

    def retrieve(self, request, pk):
        return Response({})


class DetailOnlyViewSet(viewsets.ViewSet):
    class DataWorkspace:
        table_name = "detail_only_table"
        indexes = ["one", "two", "three"]
        fields = [{"name": "id", "primary_key": True, "type": "UUID"}]

    def retrieve(self, request, pk):
        return Response({})


class HiddenFieldViewSet(viewsets.ViewSet):
    class DataWorkspace:
        table_name = "hidden_field"

    def get_serializer(self):
        return serializers.HiddenFieldSerializer()

    def list(self, request):
        return Response({})


class UUIDFieldViewSet(viewsets.ViewSet):
    class DataWorkspace:
        table_name = "uuid_field"

    def get_serializer(self):
        return serializers.UUIDFieldSerializer()

    def list(self, request):
        return Response({})


class CharFieldViewSet(viewsets.ViewSet):
    class DataWorkspace:
        table_name = "char_field"

    def get_serializer(self):
        return serializers.CharFieldSerializer()

    def list(self, request):
        return Response({})


class SerializerMethodFieldViewSet(viewsets.ViewSet):
    class DataWorkspace:
        table_name = "serializer_method_field"

    def get_serializer(self):
        return serializers.SerializerMethodFieldSerializer()

    def list(self, request):
        return Response({})


class FloatFieldViewSet(viewsets.ViewSet):
    class DataWorkspace:
        table_name = "float_field"

    def get_serializer(self):
        return serializers.FloatFieldSerializer()

    def list(self, request):
        return Response({})


class AutoPrimaryKeyViewSet(viewsets.ViewSet):
    class DataWorkspace:
        table_name = "auto_primary_key"

    def get_serializer(self):
        return serializers.AutoPrimaryKeySerializer()

    def list(self, request):
        return Response({})


class ExplicitPrimaryKeyViewSet(viewsets.ViewSet):
    class DataWorkspace:
        table_name = "explicit_primary_key"
        primary_key = "a_different_id"

    def get_serializer(self):
        return serializers.ExplicitPrimaryKeySerializer()

    def list(self, request):
        return Response({})
