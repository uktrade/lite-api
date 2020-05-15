from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from cases.enums import AdviceType
from cases.models import Advice
from conf.helpers import ensure_x_items_not_none
from conf.serializers import PrimaryKeyRelatedSerializerField, KeyValueChoiceField
from flags.enums import FlagStatuses
from goods.models import Good
from goodstype.models import GoodsType
from gov_users.serializers import GovUserListSerializer
from lite_content.lite_api import strings
from parties.enums import PartyType
from parties.models import Party
from static.countries.models import Country
from static.denial_reasons.models import DenialReason
from teams.models import Team
from teams.serializers import TeamReadOnlySerializer
from users.models import GovUser


class CaseAdviceSerializer(serializers.ModelSerializer):
    text = serializers.CharField(required=True, max_length=5000, error_messages={"blank": strings.Advice.TEXT})
    note = serializers.CharField(required=False, allow_blank=True, allow_null=True, max_length=200)
    type = KeyValueChoiceField(
        choices=AdviceType.choices, required=True, error_messages={"required": strings.Advice.TYPE}
    )
    level = serializers.CharField()
    proviso = serializers.CharField(required=False, allow_blank=True, allow_null=True, max_length=5000,)
    denial_reasons = serializers.PrimaryKeyRelatedField(queryset=DenialReason.objects.all(), many=True, required=False)
    footnote = serializers.CharField(
        required=False, allow_blank=True, error_messages={"blank": strings.Advice.FOOTNOTE}
    )
    footnote_required = serializers.BooleanField(
        required=False, error_messages={"required": strings.Advice.FOOTNOTE_REQUIRED}
    )

    user = PrimaryKeyRelatedSerializerField(queryset=GovUser.objects.all(), serializer=GovUserListSerializer)
    team = PrimaryKeyRelatedSerializerField(
        queryset=Team.objects.all(), required=False, serializer=TeamReadOnlySerializer
    )

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
    collated_pv_grading = serializers.CharField(default=None, allow_blank=True, allow_null=True, max_length=120)

    def to_representation(self, instance):
        repr_dict = super().to_representation(instance)
        fields = [
            "team",
            "end_user",
            "consignee",
            "ultimate_end_user",
            "third_party",
            "country",
            "good",
            "goods_type",
            "proviso",
            "denial_reasons",
            "pv_grading",
            "collated_pv_grading",
        ]

        for field in fields:
            if field in repr_dict and not repr_dict[field]:
                del repr_dict[field]

        return repr_dict

    def validate_denial_reasons(self, value):
        """
        Check that the denial reasons are set if type is REFUSE
        """
        for data in self.initial_data:
            if data.get("type") and data["type"] == AdviceType.REFUSE and not data["denial_reasons"]:
                raise serializers.ValidationError("Select at least one denial reason")

        return value

    def validate_proviso(self, value):
        """
        Check that the proviso is set if type is REFUSE
        """
        for data in self.initial_data:
            if data.get("type") and data["type"] == AdviceType.PROVISO and not data["proviso"]:
                raise ValidationError("Enter a proviso")

        return value

    class Meta:
        model = Advice
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super(CaseAdviceSerializer, self).__init__(*args, **kwargs)

        application_fields = (
            "good",
            "goods_type",
            "country",
            "end_user",
            "ultimate_end_user",
            "consignee",
            "third_party",
        )

        # Ensure only one item is provided
        if hasattr(self, "initial_data"):
            for data in self.initial_data:
                if not ensure_x_items_not_none([data.get(x) for x in application_fields], 1):
                    raise ValidationError({"end_user": ["Only one item (such as an end_user) can be given at a time"]})

            if self.context.get("footnote_permission"):
                self.fields["footnote_required"].required = True
                if self.initial_data[0].get("footnote_required") == "True":
                    self.fields["footnote"].required = True
                    self.fields["footnote"].allow_blank = False
                if self.initial_data[0].get("footnote_required") == "False":
                    self.fields["footnote"].allow_null = True
                    self.initial_data[0]["footnote"] = None
            else:
                self.fields["footnote"].allow_null = True
                self.initial_data[0]["footnote"] = None


class CountryWithFlagsSerializer(serializers.Serializer):
    id = serializers.CharField()
    name = serializers.CharField()
    flags = serializers.SerializerMethodField()

    def get_flags(self, instance):
        if self.context.get("active_flags_only"):
            return list(instance.flags.filter(status=FlagStatuses.ACTIVE).values("id", "name", "colour", "label"))
        else:
            return list(instance.flags.values("id", "name", "colour", "label"))
