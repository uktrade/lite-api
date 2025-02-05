from rest_framework import serializers

from api.users.models import ExporterUser


class RelatedExporterUserSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(source="baseuser_ptr_id")

    class Meta:
        model = ExporterUser
        fields = ("id", "first_name", "last_name", "email", "pending")
