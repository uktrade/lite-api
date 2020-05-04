from rest_framework import serializers

from cases.enums import AdviceType
from cases.models import Advice
from conf.serializers import PrimaryKeyRelatedSerializerField, KeyValueChoiceField
from flags.enums import FlagStatuses
from gov_users.serializers import GovUserViewSerializer
from static.denial_reasons.models import DenialReason
from users.models import GovUser


class CaseAdviceSerializerNew(serializers.Serializer):
    user = PrimaryKeyRelatedSerializerField(queryset=GovUser.objects.all(), serializer=GovUserViewSerializer)
    proviso = serializers.CharField(
        required=False,
        allow_blank=False,
        allow_null=False,
        error_messages={"blank": "Enter a proviso"},
        max_length=5000,
    )
    text = serializers.CharField(required=False, allow_blank=True, allow_null=True, max_length=5000)
    note = serializers.CharField(required=False, allow_blank=True, allow_null=True, max_length=200)
    type = KeyValueChoiceField(choices=AdviceType.choices)
    denial_reasons = serializers.PrimaryKeyRelatedField(queryset=DenialReason.objects.all(), many=True, required=False)
    level = serializers.SerializerMethodField()

    def get_level(self, instance):
        return type(Advice.objects.get_subclass(id=instance.id)).__name__


class CountryWithFlagsSerializer(serializers.Serializer):
    id = serializers.CharField()
    name = serializers.CharField()
    flags = serializers.SerializerMethodField()
    advice = CaseAdviceSerializerNew(many=True)

    def get_flags(self, instance):
        if self.context.get("active_flags_only"):
            return list(instance.flags.filter(status=FlagStatuses.ACTIVE).values("id", "name"))
        else:
            return list(instance.flags.values("id", "name"))