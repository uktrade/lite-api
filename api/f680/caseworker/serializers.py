from api.cases.generated_documents.models import GeneratedCaseDocument
from rest_framework import serializers

from api.applications.serializers.fields import CaseStatusField
from api.cases.models import Case
from api.core.serializers import CountrySerializerField, KeyValueChoiceField, PrimaryKeyRelatedField
from api.organisations.exporter.serializers import RelatedOrganisationSerializer
from api.f680 import enums
from api.f680.models import (
    F680Application,
    Product,
    Recipient,
    Recommendation,
    SecurityReleaseRequest,
    SecurityReleaseOutcome,
)
from api.teams.models import Team
from api.users.exporter.serializers import RelatedExporterUserSerializer
from api.users.enums import UserStatuses
from api.users.models import GovUser


class ProductSerializer(serializers.ModelSerializer):
    security_grading = KeyValueChoiceField(choices=enums.SecurityGrading.product_choices)

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "description",
            "security_grading",
            "security_grading_other",
        ]


class RecipientSerializer(serializers.ModelSerializer):
    country = CountrySerializerField()
    type = KeyValueChoiceField(choices=enums.RecipientType.choices)

    class Meta:
        model = Recipient
        fields = [
            "id",
            "name",
            "address",
            "country",
            "type",
            "role",
            "role_other",
        ]


class SecurityReleaseRequestSerializer(serializers.ModelSerializer):
    recipient = RecipientSerializer()
    product_id = serializers.UUIDField()
    security_grading = KeyValueChoiceField(choices=enums.SecurityGrading.security_release_choices)

    class Meta:
        model = SecurityReleaseRequest
        fields = [
            "id",
            "recipient",
            "security_grading",
            "security_grading_other",
            "approval_types",
            "intended_use",
            "product_id",
        ]


class F680ApplicationSerializer(serializers.ModelSerializer):
    status = CaseStatusField(read_only=True)
    organisation = RelatedOrganisationSerializer(read_only=True)
    submitted_by = RelatedExporterUserSerializer(read_only=True)
    security_release_requests = SecurityReleaseRequestSerializer(many=True)
    product = ProductSerializer(source="get_product")
    case_type = serializers.SerializerMethodField()

    def get_case_type(self, instance):
        from api.cases.serializers import CaseTypeSerializer

        return CaseTypeSerializer(instance.case_type).data

    class Meta:
        model = F680Application
        fields = [
            "id",
            "application",
            "status",
            "reference_code",
            "organisation",
            "submitted_at",
            "submitted_by",
            "name",
            "security_release_requests",
            "product",
            "case_type",
        ]
        read_only_fields = [
            "id",
            "status",
            "reference_code",
            "organisation",
            "submitted_at",
            "submitted_by",
            "case_type",
        ]


class F680RecommendationSerializer(serializers.ModelSerializer):
    case = PrimaryKeyRelatedField(queryset=Case.objects.all())
    user = PrimaryKeyRelatedField(queryset=GovUser.objects.filter(status=UserStatuses.ACTIVE))
    team = PrimaryKeyRelatedField(queryset=Team.objects.all())
    type = KeyValueChoiceField(choices=enums.RecommendationType.choices)
    security_grading = KeyValueChoiceField(
        choices=enums.SecurityGrading.security_release_choices, allow_blank=True, allow_null=True
    )
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

    def validate(self, data):
        if data["type"] == enums.RecommendationType.APPROVE and not data["security_grading"]:
            raise serializers.ValidationError("security_grading is required for recommendation")

        return data


class SecurityReleaseOutcomeSerializer(serializers.ModelSerializer):
    case = PrimaryKeyRelatedField(queryset=Case.objects.all())
    user = PrimaryKeyRelatedField(queryset=GovUser.objects.filter(status=UserStatuses.ACTIVE))
    team = PrimaryKeyRelatedField(queryset=Team.objects.all())
    security_release_requests = PrimaryKeyRelatedField(queryset=SecurityReleaseRequest.objects.all(), many=True)

    def validate_approve(self, data):
        if not data.get("security_grading"):
            raise serializers.ValidationError("security_grading required for approve outcome")
        if not data.get("approval_types"):
            raise serializers.ValidationError("approval_types required for approve outcome")
        if data.get("refusal_reasons"):
            raise serializers.ValidationError("refusal_reasons invalid for approve outcome")

    def validate_refuse(self, data):
        if not data.get("refusal_reasons"):
            raise serializers.ValidationError("refusal_reasons required for refuse outcome")
        if data.get("security_grading"):
            raise serializers.ValidationError("security_grading invalid for refuse outcome")
        if data.get("approval_types"):
            raise serializers.ValidationError("approval_types invalid for refuse outcome")
        if data.get("conditions"):
            raise serializers.ValidationError("conditions invalid for refuse outcome")

    def validate(self, data):
        if data["outcome"] == enums.SecurityReleaseOutcomes.APPROVE:
            self.validate_approve(data)

        if data["outcome"] == enums.SecurityReleaseOutcomes.REFUSE:
            self.validate_refuse(data)

        existing_outcomes = SecurityReleaseOutcome.objects.filter(
            security_release_requests__in=data["security_release_requests"]
        ).exists()
        if existing_outcomes:
            raise serializers.ValidationError(
                "A SecurityReleaseOutcome record exists for one or more of the security release ids"
            )

        return data

    class Meta:
        model = SecurityReleaseOutcome
        fields = [
            "id",
            "case",
            "user",
            "team",
            "security_release_requests",
            "outcome",
            "conditions",
            "refusal_reasons",
            "security_grading",
            "approval_types",
            "validity_start_date",
            "validity_end_date",
            "validity_period",
        ]


class SecurityReleaseOutcomeLetterSerializer(serializers.ModelSerializer):
    security_release_requests = SecurityReleaseRequestSerializer(many=True)
    approval_types = serializers.MultipleChoiceField(choices=enums.ApprovalTypes.choices)
    validity_end_date = serializers.DateField(format="%d %B %Y")

    class Meta:
        model = SecurityReleaseOutcome
        fields = [
            "security_release_requests",
            "outcome",
            "conditions",
            "refusal_reasons",
            "security_grading",
            "approval_types",
            "validity_start_date",
            "validity_end_date",
            "validity_period",
        ]


class OutcomeDocumentSerializer(serializers.ModelSerializer):

    class Meta:
        model = GeneratedCaseDocument
        fields = (
            "id",
            "template",
            "name",
            "visible_to_exporter",
        )
        
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        approval_types_dict = dict(enums.ApprovalTypes.choices)
        all_activities = instance.security_release_requests.first().approval_types

        if instance.outcome == enums.SecurityReleaseOutcomes.APPROVE:
            approved = instance.approval_types
            refused = list(set(all_activities) - set(approved))

            representation["approval_types"] = [
                {"key": key, "value": approval_types_dict[key], "status": "Approved"} for key in approved
            ]
            representation["approval_types"].extend(
                [{"key": key, "value": approval_types_dict[key], "status": "Refused"} for key in refused]
            )
        elif instance.outcome == enums.SecurityReleaseOutcomes.REFUSE:
            representation["approval_types"] = [
                {"key": key, "value": approval_types_dict[key], "status": "Refused"} for key in all_activities
            ]

        return representation
