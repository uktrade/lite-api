from rest_framework import serializers
from rest_framework.relations import PrimaryKeyRelatedField

from api.applications.enums import GoodsTypeCategory
from api.applications.models import OpenApplication
from api.applications.mixins.serializers import PartiesSerializerMixin
from api.core.serializers import KeyValueChoiceField
from api.organisations.models import Organisation
from api.staticdata.statuses.enums import CaseStatusEnum
from api.staticdata.statuses.libraries.get_case_status import get_case_status_by_status


from .generic_application import (
    GenericApplicationCreateSerializer,
    GenericApplicationViewSerializer,
)


class OpenApplicationCreateSerializer(serializers.ModelSerializer):
    organisation = PrimaryKeyRelatedField(queryset=Organisation.objects.all())

    class Meta:
        model = OpenApplication
        fields = GenericApplicationCreateSerializer.Meta.fields + ("goods_category",)

    def __init__(self, case_type_id, **kwargs):
        super().__init__(**kwargs)
        self.initial_data["case_type"] = case_type_id
        self.initial_data["organisation"] = self.context.id

    def create(self, validated_data):
        validated_data["status"] = get_case_status_by_status(CaseStatusEnum.DRAFT)
        return super().create(validated_data)


class OpenApplicationUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = OpenApplication
        fields = ("name",)


class OpenApplicationViewSerializer(PartiesSerializerMixin, GenericApplicationViewSerializer):
    goods_category = KeyValueChoiceField(choices=GoodsTypeCategory.choices)

    class Meta:
        model = OpenApplication
        fields = GenericApplicationViewSerializer.Meta.fields + ("goods_category",)
