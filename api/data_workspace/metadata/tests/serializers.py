import datetime

from typing import Optional

from rest_framework import serializers


class HiddenFieldSerializer(serializers.Serializer):
    hidden_field = serializers.HiddenField(default="")


class UUIDFieldSerializer(serializers.Serializer):
    uuid_field = serializers.UUIDField()
    nullable_uuid_field = serializers.UUIDField(allow_null=True)


class CharFieldSerializer(serializers.Serializer):
    char_field = serializers.CharField()
    nullable_char_field = serializers.CharField(allow_null=True)


class SerializerMethodFieldSerializer(serializers.Serializer):
    returns_string = serializers.SerializerMethodField()
    returns_optional_string = serializers.SerializerMethodField()
    returns_datetime = serializers.SerializerMethodField()
    returns_optional_datetime = serializers.SerializerMethodField()

    def get_returns_string(self, instance) -> str:
        return "string"

    def get_returns_optional_string(self, instance) -> Optional[str]:
        return None

    def get_returns_datetime(self, instance) -> datetime.datetime:
        return datetime.datetime.now()

    def get_returns_optional_datetime(self, instance) -> Optional[datetime.datetime]:
        return None


class AutoPrimaryKeySerializer(serializers.Serializer):
    id = serializers.UUIDField()
    not_a_primary_key = serializers.UUIDField()


class ExplicitPrimaryKeySerializer(serializers.Serializer):
    a_different_id = serializers.UUIDField()
    not_a_primary_key = serializers.UUIDField()
