from rest_framework import serializers

from cases.models import CaseType
from cases.serializers import CaseTypeSerializer
from api.conf.serializers import PrimaryKeyRelatedSerializerField, CountrySerializerField
from api.flags.models import Flag
from api.flags.serializers import FlagSerializer
from lite_content.lite_api import strings
from api.queues.models import Queue
from api.queues.serializers import TinyQueueSerializer
from static.statuses.models import CaseStatus
from static.statuses.serializers import CaseStatusSerializer
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
    flags = PrimaryKeyRelatedSerializerField(
        queryset=Flag.objects.all(),
        serializer=FlagSerializer,
        many=True,
        required=False,
        allow_null=True,
        allow_empty=True,
        error_messages={"required": strings.RoutingRules.Errors.NO_FLAGS},
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
            "flags",
            "case_types",
            "additional_rules",
            "active",
        )

    def __init__(self, *args, **kwargs):
        # set fields to required or not depending on additional rules passed forward
        super().__init__(*args, **kwargs)
        if kwargs.get("data"):
            if not kwargs["data"].get("team"):
                self.initial_data["team"] = kwargs["context"]["request"].user.team_id

            additional_rules = kwargs["data"].get("additional_rules")
            if not isinstance(additional_rules, list):
                additional_rules = [additional_rules]

            if RoutingRulesAdditionalFields.USERS in additional_rules:
                self.fields["user"].required = True
                self.fields["user"].allow_null = False
            else:
                self.initial_data["user"] = None

            if RoutingRulesAdditionalFields.CASE_TYPES in additional_rules:
                self.fields["case_types"].required = True
                self.fields["case_types"].allow_null = False
                self.fields["case_types"].allow_empty = False
            else:
                self.initial_data["case_types"] = []

            if RoutingRulesAdditionalFields.COUNTRY in additional_rules:
                self.fields["country"].required = True
                self.fields["country"].allow_null = False
            else:
                self.initial_data["country"] = None

            if RoutingRulesAdditionalFields.FLAGS in additional_rules:
                self.fields["flags"].required = True
                self.fields["flags"].allow_null = False
                self.fields["flags"].allow_empty = False
            else:
                self.initial_data["flags"] = []


# flattened serializer for editing purposes
class SmallRoutingRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = RoutingRule
        fields = "__all__"
