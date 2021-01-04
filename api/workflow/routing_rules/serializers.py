from rest_framework import serializers

from api.cases.models import CaseType
from api.cases.serializers import CaseTypeSerializer
from api.core.serializers import PrimaryKeyRelatedSerializerField, CountrySerializerField
from api.flags.models import Flag
from api.flags.serializers import FlagSerializer
from lite_content.lite_api import strings
from api.queues.models import Queue
from api.queues.serializers import TinyQueueSerializer
from api.staticdata.statuses.models import CaseStatus
from api.staticdata.statuses.serializers import CaseStatusSerializer
from api.teams.models import Team
from api.teams.serializers import TeamSerializer
from api.users.models import GovUser
from api.gov_users.serializers import GovUserViewSerializer
from api.workflow.routing_rules.enum import RoutingRulesAdditionalFields
from api.workflow.routing_rules.models import RoutingRule


class RoutingRuleSerializer(serializers.ModelSerializer):
    team = PrimaryKeyRelatedSerializerField(queryset=Team.objects.all(), serializer=TeamSerializer)
    queue = PrimaryKeyRelatedSerializerField(
        queryset=Queue.objects.all(),
        serializer=TinyQueueSerializer,
        error_messages={"required": strings.RoutingRules.Errors.NO_QUEUE, "null": strings.RoutingRules.Errors.NO_QUEUE},
    )
    status = PrimaryKeyRelatedSerializerField(
        queryset=CaseStatus.objects.all(),
        serializer=CaseStatusSerializer,
        error_messages={
            "required": strings.RoutingRules.Errors.NO_CASE_STATUS,
            "null": strings.RoutingRules.Errors.NO_CASE_STATUS,
        },
    )
    tier = serializers.IntegerField(
        min_value=1,
        max_value=32000,
        error_messages={
            "required": strings.RoutingRules.Errors.INVALID_TIER,
            "invalid": strings.RoutingRules.Errors.INVALID_TIER,
        },
    )
    additional_rules = serializers.MultipleChoiceField(
        choices=RoutingRulesAdditionalFields.choices, allow_empty=True, required=False
    )

    user = PrimaryKeyRelatedSerializerField(
        queryset=GovUser.objects.all(),
        serializer=GovUserViewSerializer,
        required=False,
        allow_null=True,
        error_messages={"required": strings.RoutingRules.Errors.NO_USER},
    )
    case_types = PrimaryKeyRelatedSerializerField(
        queryset=CaseType.objects.all(),
        serializer=CaseTypeSerializer,
        many=True,
        required=False,
        allow_null=True,
        allow_empty=True,
        error_messages={"required": strings.RoutingRules.Errors.NO_CASE_TYPE},
    )
    flags_to_include = PrimaryKeyRelatedSerializerField(
        queryset=Flag.objects.all(),
        serializer=FlagSerializer,
        many=True,
        required=False,
        allow_null=True,
        allow_empty=True,
    )
    flags_to_exclude = PrimaryKeyRelatedSerializerField(
        queryset=Flag.objects.all(),
        serializer=FlagSerializer,
        many=True,
        required=False,
        allow_null=True,
        allow_empty=True,
    )
    country = CountrySerializerField(
        required=False, allow_null=True, error_messages={"required": strings.RoutingRules.Errors.NO_COUNTRY},
    )

    class Meta:
        model = RoutingRule
        fields = (
            "id",
            "team",
            "queue",
            "status",
            "tier",
            "user",
            "case_types",
            "country",
            "flags_to_include",
            "flags_to_exclude",
            "case_types",
            "additional_rules",
            "active",
        )

    def __init__(self, *args, **kwargs):
        # set fields to required or not depending on additional rules passed forward
        super().__init__(*args, **kwargs)
        if kwargs.get("data"):
            if not kwargs["data"].get("team"):
                self.initial_data["team"] = kwargs["context"]["request"].user.govuser.team.id

            additional_rules = kwargs["data"].get("additional_rules")
            if not isinstance(additional_rules, list):
                additional_rules = [additional_rules]

            if RoutingRulesAdditionalFields.USERS not in additional_rules:
                self.initial_data["user"] = None

            if RoutingRulesAdditionalFields.CASE_TYPES not in additional_rules:
                self.initial_data["case_types"] = []

            if RoutingRulesAdditionalFields.COUNTRY not in additional_rules:
                self.initial_data["country"] = None

            if RoutingRulesAdditionalFields.FLAGS not in additional_rules:
                self.initial_data["flags_to_include"] = []
                self.initial_data["flags_to_exclude"] = []

    def validate(self, data):
        validated_data = super().validate(data)
        additional_rules = validated_data.get("additional_rules")

        if "case_types" in additional_rules and "case_types" not in validated_data:
            raise serializers.ValidationError({"case_types[]": "Select a case type"})

        if "flags" in additional_rules:
            if not validated_data.get("flags_to_include") and not validated_data.get("flags_to_exclude"):
                raise serializers.ValidationError({"routing_rules_flags_condition": "Select a flag and flag condition"})

        if "country" in additional_rules:
            if "country" not in validated_data or validated_data.get("country") is None:
                raise serializers.ValidationError({"country": "Select a country"})

        if "users" in additional_rules:
            if "user" not in validated_data:
                raise serializers.ValidationError({"user": "Select a user"})

        return validated_data


# flattened serializer for editing purposes
class SmallRoutingRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = RoutingRule
        fields = "__all__"
        read_only_fields = (
            "id",
            "team",
            "status",
            "queue",
            "tier",
            "additional_rules",
            "active",
            "case_types",
            "user",
            "country",
            "flags_to_include",
            "flags_to_exclude",
        )
