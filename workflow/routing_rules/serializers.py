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
from workflow.routing_rules.models import RoutingRule


class RoutingRuleSerializer(serializers.ModelSerializer):
    team = PrimaryKeyRelatedSerializerField(queryset=Team.objects.all(), serializer=TeamSerializer)
    queue = PrimaryKeyRelatedSerializerField(queryset=Queue.objects.all(), serializer=TinyQueueSerializer)
    status = PrimaryKeyRelatedSerializerField(queryset=CaseStatus.objects.all(), serializer=CaseStatusSerializer)
    tier = serializers.IntegerField(max_value=32000)

    user = PrimaryKeyRelatedSerializerField(queryset=GovUser.objects.all(), serializer=GovUserViewSerializer)

    case_types = PrimaryKeyRelatedSerializerField(
        queryset=CaseType.objects.all(), serializer=CaseTypeSerializer, many=True
    )
    flags = PrimaryKeyRelatedSerializerField(queryset=Flag.objects.all(), serializer=FlagSerializer, many=True)
    country = CountrySerializerField()

    class Meta:
        model = RoutingRule
        fields = ("id", "team", "queue", "status", "tier", "user", "case_types", "country", "flags", "case_types")
