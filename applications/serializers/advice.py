from rest_framework import serializers

from cases.enums import AdviceType
from cases.models import Advice
from conf.serializers import PrimaryKeyRelatedSerializerField, KeyValueChoiceField
from flags.enums import FlagStatuses
from goods.models import Good
from goodstype.models import GoodsType
from gov_users.serializers import GovUserListSerializer
from parties.enums import PartyType
from parties.models import Party
from static.countries.models import Country
from static.denial_reasons.models import DenialReason
from teams.serializers import TeamReadOnlySerializer
from users.models import GovUser


class CaseAdviceSerializerNew(serializers.Serializer):
    user = PrimaryKeyRelatedSerializerField(queryset=GovUser.objects.all(), serializer=GovUserListSerializer)
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
    level = serializers.CharField()
    team = TeamReadOnlySerializer()

    good = serializers.PrimaryKeyRelatedField(queryset=Good.objects.all(), required=False)
    goods_type = serializers.PrimaryKeyRelatedField(queryset=GoodsType.objects.all(), required=False)
    country = serializers.PrimaryKeyRelatedField(queryset=Country.objects.all(), required=False)
    end_user = serializers.PrimaryKeyRelatedField(
        queryset=Party.objects.filter(type=PartyType.END_USER), required=False
    )
    ultimate_end_user = serializers.PrimaryKeyRelatedField(
        queryset=Party.objects.filter(type=PartyType.ULTIMATE_END_USER), required=False
    )
    consignee = serializers.PrimaryKeyRelatedField(
        queryset=Party.objects.filter(type=PartyType.CONSIGNEE), required=False
    )
    third_party = serializers.PrimaryKeyRelatedField(
        queryset=Party.objects.filter(type=PartyType.THIRD_PARTY), required=False
    )

    def to_representation(self, instance):
        repr_dict = super().to_representation(instance)
        entities = ["team", "end_user", "consignee", "ultimate_end_user", "third_party", "country", "good", "goods_type"]

        for entity in entities:
            if entity in repr_dict and not repr_dict[entity]:
                del repr_dict[entity]

        return repr_dict


class CountryWithFlagsSerializer(serializers.Serializer):
    id = serializers.CharField()
    name = serializers.CharField()
    flags = serializers.SerializerMethodField()

    def get_flags(self, instance):
        if self.context.get("active_flags_only"):
            return list(instance.flags.filter(status=FlagStatuses.ACTIVE).values("id", "name"))
        else:
            return list(instance.flags.values("id", "name"))
