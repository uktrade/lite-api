from rest_framework import serializers

from api.core.serializers import KeyValueChoiceField, PrimaryKeyRelatedField
from api.f680.enums import RecipientType, RecommendationType, SecurityGrading
from api.f680.models import F680Application, Recommendation, SecurityReleaseRequest


class CountryViewSerializer(serializers.Serializer):
    id = serializers.UUIDField(read_only=True)
    name = serializers.CharField(read_only=True)


class TeamViewSerializer(serializers.Serializer):
    id = serializers.UUIDField(read_only=True)
    name = serializers.CharField(read_only=True)
    alias = serializers.CharField(read_only=True)


class GovUserViewSerializer(serializers.Serializer):
    id = serializers.ReadOnlyField(source="baseuser_ptr_id")
    first_name = serializers.CharField(read_only=True)
    last_name = serializers.CharField(read_only=True)
    team = TeamViewSerializer()


class F680ProductViewSerializer(serializers.Serializer):
    name = serializers.CharField(read_only=True)
    description = serializers.CharField(read_only=True)
    security_grading = KeyValueChoiceField(choices=SecurityGrading.product_choices)
    security_grading_other = serializers.CharField(read_only=True)


class F680RecipientViewSerializer(serializers.Serializer):
    name = serializers.CharField(read_only=True)
    address = serializers.CharField(read_only=True)
    country = CountryViewSerializer()
    type = KeyValueChoiceField(choices=RecipientType.choices)


class F680SecurityReleaseRequestSerializer(serializers.Serializer):
    recipient = F680RecipientViewSerializer()
    product = F680ProductViewSerializer()
    security_grading = KeyValueChoiceField(choices=SecurityGrading.security_release_choices)
    security_grading_other = serializers.CharField(read_only=True)
    approval_types = serializers.ListField(child=serializers.CharField(read_only=True))
    intended_use = serializers.CharField(read_only=True)


class F680RecommendationViewSerializer(serializers.ModelSerializer):
    case = serializers.ReadOnlyField(source="case_id")
    user = GovUserViewSerializer()
    team = TeamViewSerializer()
    type = KeyValueChoiceField(choices=RecommendationType.choices)
    security_grading = KeyValueChoiceField(choices=SecurityGrading.security_release_choices)
    security_release_request = F680SecurityReleaseRequestSerializer()

    class Meta:
        model = Recommendation
        fields = (
            "id",
            "created_at",
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
        read_only_fields = fields
