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
    tier = serializers.IntegerField(min_value=1, max_value=32000)
    additional_rules = serializers.MultipleChoiceField(
        choices=RoutingRulesAdditionalFields.choices, allow_empty=True, required=False
    )

    user = PrimaryKeyRelatedSerializerField(
        queryset=GovUser.objects.all(), serializer=GovUserViewSerializer, required=False, allow_null=True,
    )
    case_types = PrimaryKeyRelatedSerializerField(
        queryset=CaseType.objects.all(),
        serializer=CaseTypeSerializer,
        many=True,
        required=False,
        allow_null=True,
        allow_empty=True,
    )
    flags = PrimaryKeyRelatedSerializerField(
        queryset=Flag.objects.all(),
        serializer=FlagSerializer,
        many=True,
        required=False,
        allow_null=True,
        allow_empty=True,
    )
    country = CountrySerializerField(required=False, allow_null=True,)

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

    def update(self, instance, validated_data):
        instance.queue = validated_data.get("queue", instance.queue)
        instance.tier = validated_data.get("tier", instance.tier)
        instance.status = validated_data.get("status", instance.status)

        instance.additional_rules = validated_data.get("additional_rules", instance.additional_rules)

        instance.user = validated_data.get("user", instance.user)
        instance.country = validated_data.get("country", instance.country)
        instance.case_types.set(validated_data.get("case_types", instance.case_types.all()))
        instance.flags.set(validated_data.get("flags", instance.flags.all()))

        instance.save()
        return instance


# flattened serializer for editing purposes
class SmallRoutingRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = RoutingRule
        fields = "__all__"
