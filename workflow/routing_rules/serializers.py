from rest_framework import serializers

from cases.models import CaseType
from cases.serializers import CaseTypeSerializer
from conf.serializers import PrimaryKeyRelatedSerializerField, CountrySerializerField
from flags.models import Flag
from flags.serializers import FlagSerializer
from queues.models import Queue
from queues.serializers import TinyQueueSerializer
from static.statuses.models import CaseStatus
from static.statuses.serializers import CaseStatusSerializer
from teams.models import Team
from teams.serializers import TeamSerializer
from users.models import GovUser
from users.serializers import GovUserViewSerializer
from workflow.routing_rules.enum import RoutingRulesAdditionalFields
from workflow.routing_rules.models import RoutingRule


class RoutingRuleSerializer(serializers.ModelSerializer):
    team = PrimaryKeyRelatedSerializerField(queryset=Team.objects.all(), serializer=TeamSerializer)
    queue = PrimaryKeyRelatedSerializerField(queryset=Queue.objects.all(), serializer=TinyQueueSerializer)
    status = PrimaryKeyRelatedSerializerField(queryset=CaseStatus.objects.all(), serializer=CaseStatusSerializer)
    tier = serializers.IntegerField(min_value=0, max_value=32000)
    additional_rules = serializers.MultipleChoiceField(
        choices=RoutingRulesAdditionalFields.choices, allow_empty=True, required=False
    )

    user = PrimaryKeyRelatedSerializerField(
        queryset=GovUser.objects.all(), serializer=GovUserViewSerializer, required=False
    )
    case_types = PrimaryKeyRelatedSerializerField(
        queryset=CaseType.objects.all(), serializer=CaseTypeSerializer, many=True, required=False
    )
    flags = PrimaryKeyRelatedSerializerField(
        queryset=Flag.objects.all(), serializer=FlagSerializer, many=True, required=False
    )
    country = CountrySerializerField(required=False)

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
        # set fields to required or not depending on array passed forward
        super().__init__(*args, **kwargs)
        if kwargs.get("data"):
            if not kwargs["data"].get("team"):
                self.initial_data["team"] = kwargs["context"]["request"].user.team_id
            additional_rules = kwargs["data"].get("additional_rules", [])

            if RoutingRulesAdditionalFields.USERS in additional_rules:
                self.fields["user"].required = True

            if RoutingRulesAdditionalFields.CASE_TYPES in additional_rules:
                self.fields["case_types"].required = True

            if RoutingRulesAdditionalFields.COUNTRY in additional_rules:
                self.fields["country"].required = True

            if RoutingRulesAdditionalFields.FLAGS in additional_rules:
                self.fields["flags"].required = True
