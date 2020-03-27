from rest_framework import serializers
from rest_framework.relations import PrimaryKeyRelatedField

from applications.models import (
    BaseApplication,
    ExternalLocationOnApplication,
)
from organisations.models import ExternalLocation


class ExternalLocationOnApplicationSerializer(serializers.ModelSerializer):
    application = PrimaryKeyRelatedField(queryset=BaseApplication.objects.all())
    external_location = PrimaryKeyRelatedField(queryset=ExternalLocation.objects.all())

    class Meta:
        model = ExternalLocationOnApplication
        fields = (
            "id",
            "external_location",
            "application",
        )
