from rest_framework import serializers

from api.applications.serializers.fields import CaseStatusField
from api.cases.models import Case
from api.core.serializers import KeyValueChoiceField, PrimaryKeyRelatedField
from api.organisations.exporter.serializers import RelatedOrganisationSerializer
from api.f680.enums import RecommendationType, SecurityGrading
from api.f680.models import F680Application, Recommendation, SecurityReleaseRequest
from api.teams.models import Team
from api.users.exporter.serializers import RelatedExporterUserSerializer
from api.users.enums import UserStatuses
from api.users.models import GovUser


class F680ApplicationSerializer(serializers.ModelSerializer):  # /PS-IGNORE
    status = CaseStatusField(read_only=True)
    organisation = RelatedOrganisationSerializer(read_only=True)
    submitted_by = RelatedExporterUserSerializer(read_only=True)

    class Meta:
        model = F680Application  # /PS-IGNORE
        fields = [
            "id",
            "application",
            "status",
            "reference_code",
            "organisation",
            "submitted_at",
            "submitted_by",
            "name",
        ]
        read_only_fields = ["id", "status", "reference_code", "organisation", "submitted_at", "submitted_by"]


class F680RecommendationSerializer(serializers.ModelSerializer):
    case = PrimaryKeyRelatedField(queryset=Case.objects.all())
    user = PrimaryKeyRelatedField(queryset=GovUser.objects.filter(status=UserStatuses.ACTIVE))
    team = PrimaryKeyRelatedField(queryset=Team.objects.all())
    type = KeyValueChoiceField(choices=RecommendationType.choices)
    security_grading = KeyValueChoiceField(choices=SecurityGrading.security_release_choices)
    security_grading_other = serializers.CharField(allow_blank=True, allow_null=True, required=False)
    conditions = serializers.CharField(allow_blank=True, allow_null=True)
    refusal_reasons = serializers.CharField(allow_blank=True, allow_null=True)
    security_release_request = PrimaryKeyRelatedField(queryset=SecurityReleaseRequest.objects.all())

    class Meta:
        model = Recommendation
        fields = (
            "id",
            "type",
            "security_grading",
            "security_grading_other",
            "conditions",
            "refusal_reasons",
            "user",
            "team",
            "case",
            "security_release_request",
        )
        read_only_fields = ["id"]
