from django.db.models import Q
from rest_framework import serializers
from rest_framework.relations import PrimaryKeyRelatedField

from api.applications.enums import GoodsTypeCategory
from api.applications.models import OpenApplication
from api.applications.mixins.serializers import PartiesSerializerMixin
from api.appeals.serializers import AppealSerializer
from api.audit_trail.models import Audit
from api.audit_trail.enums import AuditType
from api.core.serializers import KeyValueChoiceField
from api.cases.models import CaseType
from api.licences.models import Licence
from api.licences.serializers.view_licence import CaseLicenceViewSerializer
from api.organisations.models import Organisation
from api.staticdata.statuses.enums import CaseStatusEnum
from api.staticdata.statuses.serializers import CaseSubStatusSerializer
from api.staticdata.statuses.libraries.get_case_status import get_case_status_by_status
from .denial import DenialMatchOnApplicationViewSerializer
from .good import GoodOnApplicationViewSerializer

from .generic_application import (
    GenericApplicationViewSerializer,
)


class OpenApplicationCreateSerializer(serializers.ModelSerializer):
    organisation = PrimaryKeyRelatedField(queryset=Organisation.objects.all())

    class Meta:
        model = OpenApplication
        fields = (
            "id",
            "name",
            "goods_category",
            "organisation",
        )

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

    class Meta:
        model = OpenApplication
        fields = GenericApplicationViewSerializer.Meta.fields
