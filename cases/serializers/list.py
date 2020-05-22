from rest_framework import serializers

from cases.enums import CaseTypeReferenceEnum, CaseTypeTypeEnum, CaseTypeSubTypeEnum
from cases.fields import CaseAssignmentRelatedSerializerField, HasOpenECJUQueriesRelatedField
from cases.libraries.get_flags import get_ordered_flags
from cases.models import CaseType
from conf.serializers import PrimaryKeyRelatedSerializerField, KeyValueChoiceField
from organisations.models import Organisation
from organisations.serializers import OrganisationCaseSerializer
from static.statuses.enums import CaseStatusEnum


class CaseTypeSerializer(serializers.ModelSerializer):
    reference = KeyValueChoiceField(choices=CaseTypeReferenceEnum.choices)
    type = KeyValueChoiceField(choices=CaseTypeTypeEnum.choices)
    sub_type = KeyValueChoiceField(choices=CaseTypeSubTypeEnum.choices)

    class Meta:
        model = CaseType
        fields = (
            "id",
            "reference",
            "type",
            "sub_type",
        )


class CaseListSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    reference_code = serializers.CharField()
    case_type = PrimaryKeyRelatedSerializerField(queryset=CaseType.objects.all(), serializer=CaseTypeSerializer)
    assignments = CaseAssignmentRelatedSerializerField(source="case_assignments")
    status = serializers.SerializerMethodField()
    flags = serializers.SerializerMethodField()
    submitted_at = serializers.SerializerMethodField()
    sla_days = serializers.IntegerField()
    sla_remaining_days = serializers.IntegerField()
    has_open_ecju_queries = HasOpenECJUQueriesRelatedField(source="case_ecju_query")
    organisation = PrimaryKeyRelatedSerializerField(
        queryset=Organisation.objects.all(), serializer=OrganisationCaseSerializer
    )

    def __init__(self, *args, **kwargs):
        self.team = kwargs.pop("team", None)
        self.include_hidden = kwargs.pop("include_hidden", None)
        super().__init__(*args, **kwargs)

    def get_flags(self, instance):
        """
        Gets flags for a case and returns in sorted order by team.
        """
        return get_ordered_flags(instance, self.team)

    def get_submitted_at(self, instance):
        # Return the DateTime value manually as otherwise
        # it'll return a string representation which isn't suitable for filtering
        return instance.submitted_at

    def get_status(self, instance):
        return {"key": instance.status.status, "value": CaseStatusEnum.get_text(instance.status.status)}
