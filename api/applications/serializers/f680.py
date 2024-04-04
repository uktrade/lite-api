from rest_framework import serializers
from rest_framework.relations import PrimaryKeyRelatedField

from api.applications.models import F680Application
from api.cases.models import CaseType
from api.organisations.models import Organisation
from api.staticdata.statuses.enums import CaseStatusEnum
from api.staticdata.statuses.libraries.get_case_status import get_case_status_by_status


class F680ApplicationCreateSerializer(serializers.ModelSerializer):
    case_type = PrimaryKeyRelatedField(
        queryset=CaseType.objects.all(),
    )
    organisation = PrimaryKeyRelatedField(queryset=Organisation.objects.all())

    class Meta:
        model = F680Application
        fields = (
            "id",
            "name",
            "case_type",
            "organisation",
        )

    def __init__(self, case_type_id, **kwargs):
        super().__init__(**kwargs)
        self.initial_data["case_type"] = case_type_id
        self.initial_data["organisation"] = self.context.id

    def create(self, validated_data):
        validated_data["status"] = get_case_status_by_status(CaseStatusEnum.DRAFT)
        return super().create(validated_data)
