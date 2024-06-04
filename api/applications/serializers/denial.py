from rest_framework import serializers
from rest_framework.fields import ChoiceField

from api.applications.models import BaseApplication, DenialMatchOnApplication
from api.external_data.enums import DenialMatchCategory
from api.external_data.models import DenialEntity
from api.external_data.serializers import DenialEntitySerializer


class DenialMatchOnApplicationViewSerializer(serializers.ModelSerializer):
    category = ChoiceField(choices=DenialMatchCategory.choices)
    denial_entity = DenialEntitySerializer(read_only=True)
    denial = serializers.SerializerMethodField()

    class Meta:
        model = DenialMatchOnApplication
        fields = ("id", "application", "denial", "denial_entity", "category")

    def get_denial(self, instance):
        # This field is for backward compatablity to be remove once FE has been updated.
        return DenialEntitySerializer(instance.denial_entity).data


class DenialMatchOnApplicationCreateSerializer(serializers.ModelSerializer):
    application = serializers.PrimaryKeyRelatedField(queryset=BaseApplication.objects.all())
    category = ChoiceField(choices=DenialMatchCategory.choices)
    denial_entity = serializers.PrimaryKeyRelatedField(queryset=DenialEntity.objects.all())

    class Meta:
        model = DenialMatchOnApplication
        fields = ("id", "application", "denial_entity", "category")
