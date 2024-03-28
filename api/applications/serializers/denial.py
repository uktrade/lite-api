from rest_framework import serializers
from rest_framework.fields import ChoiceField

from api.applications.models import BaseApplication, DenialMatchOnApplication
from api.external_data.enums import DenialMatchCategory
from api.external_data.models import DenialEntity
from api.external_data.serializers import DenialEntitySerializer


class DenialMatchOnApplicationViewSerializer(serializers.ModelSerializer):
    category = ChoiceField(choices=DenialMatchCategory.choices)
    denial = DenialEntitySerializer(read_only=True)

    class Meta:
        model = DenialMatchOnApplication
        fields = ("id", "application", "denial", "category")


class DenialMatchOnApplicationCreateSerializer(serializers.ModelSerializer):
    application = serializers.PrimaryKeyRelatedField(queryset=BaseApplication.objects.all())
    category = ChoiceField(choices=DenialMatchCategory.choices)
    denial = serializers.PrimaryKeyRelatedField(queryset=DenialEntity.objects.all())

    class Meta:
        model = DenialMatchOnApplication
        fields = ("id", "application", "denial", "category")
