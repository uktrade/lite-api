from rest_framework import serializers

from api.core.serializers import KeyValueChoiceField
from api.f680.enums import RecommendationType, SecurityGrading
from api.f680.models import Recommendation


class TeamViewSerializer(serializers.Serializer):
    id = serializers.UUIDField(read_only=True)
    name = serializers.CharField(read_only=True)
    alias = serializers.CharField(read_only=True)


class GovUserViewSerializer(serializers.Serializer):
    id = serializers.ReadOnlyField(source="baseuser_ptr_id")
    first_name = serializers.CharField(read_only=True)
    last_name = serializers.CharField(read_only=True)
    team = serializers.ReadOnlyField(source="team_id")


class F680RecommendationViewSerializer(serializers.ModelSerializer):
    case = serializers.ReadOnlyField(source="case_id")
    user = GovUserViewSerializer()
    team = TeamViewSerializer()
    type = KeyValueChoiceField(choices=RecommendationType.choices)
    security_grading = KeyValueChoiceField(choices=SecurityGrading.security_release_choices)

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
