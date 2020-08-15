from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from api.cases.enums import AdviceType
from api.cases.models import Advice
from api.conf.serializers import PrimaryKeyRelatedSerializerField, KeyValueChoiceField
from api.flags.enums import FlagStatuses
from api.goods.models import Good
from api.goodstype.models import GoodsType
from api.gov_users.serializers import GovUserListSerializer
from lite_content.lite_api import strings
from api.parties.enums import PartyType
from api.parties.models import Party
from api.staticdata.countries.models import Country
from api.staticdata.denial_reasons.models import DenialReason
from api.teams.models import Team
from api.teams.serializers import TeamReadOnlySerializer
from api.users.models import GovUser


class AdviceViewSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    text = serializers.CharField()
    note = serializers.CharField()
    type = KeyValueChoiceField(choices=AdviceType.choices)
    level = serializers.CharField()
    proviso = serializers.CharField()
    denial_reasons = serializers.PrimaryKeyRelatedField(queryset=DenialReason.objects.all(), many=True)
    footnote = serializers.CharField()
    user = PrimaryKeyRelatedSerializerField(queryset=GovUser.objects.all(), serializer=GovUserListSerializer)
    created_at = serializers.DateTimeField()

    good = serializers.UUIDField(source="good_id")
    goods_type = serializers.UUIDField(source="goods_type_id")
    country = serializers.UUIDField(source="country_id")
    end_user = serializers.UUIDField(source="end_user_id")
    ultimate_end_user = serializers.UUIDField(source="ultimate_end_user_id")
    consignee = serializers.UUIDField(source="consignee_id")
    third_party = serializers.UUIDField(source="third_party_id")


class AdviceCreateSerializer(serializers.ModelSerializer):
    text = serializers.CharField(required=True, max_length=5000, error_messages={"blank": strings.Advice.TEXT})
    note = serializers.CharField(required=False, allow_blank=True, allow_null=True, max_length=200)
    type = KeyValueChoiceField(
        choices=AdviceType.choices, required=True, error_messages={"required": strings.Advice.TYPE}
    )
    level = serializers.CharField()
    proviso = serializers.CharField(required=False, allow_blank=True, allow_null=True, max_length=5000,)
    denial_reasons = serializers.PrimaryKeyRelatedField(queryset=DenialReason.objects.all(), many=True, required=False)
    footnote = serializers.CharField(
        required=False, allow_blank=True, allow_null=True, error_messages={"blank": strings.Advice.FOOTNOTE}
    )
    footnote_required = serializers.BooleanField(
        required=False, allow_null=True, error_messages={"required": strings.Advice.FOOTNOTE_REQUIRED}
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
        return AdviceViewSerializer(instance).data

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
        super(AdviceCreateSerializer, self).__init__(*args, **kwargs)

        if hasattr(self, "initial_data"):
            self._footnote_fields_setup()

            # Only require a reason for the advice decision if it is of type refuse
            if self.initial_data[0].get("type") != AdviceType.REFUSE:
                self.fields["text"].required = False
                self.fields["text"].allow_null = True
                self.fields["text"].allow_blank = True

    def _footnote_fields_setup(self):
        # if the user has permission to maintain footnotes for advice,
        #  they have to explicitly state if a footnote is required.
        if self.context.get("footnote_permission"):
            self.fields["footnote_required"].required = True
            self.fields["footnote_required"].allow_null = False
            # if a footnote is required, we have to validate each footnote is given
            if self.initial_data[0].get("footnote_required") == "True":
                self.fields["footnote"].required = True
                self.fields["footnote"].allow_null = False
                self.fields["footnote"].allow_blank = False
            # if a footnote is not required, we remove any footnotes that may already exist on the objects.
            if self.initial_data[0].get("footnote_required") == "False":
                for i in range(0, len(self.initial_data)):
                    self.initial_data[i]["footnote"] = None
        else:
            # If the user does not have permission, we do not allow the user to set any footnote details.
            for i in range(0, len(self.initial_data)):
                self.initial_data[i]["footnote"] = None
                self.initial_data[i]["footnote_required"] = None


class CountryWithFlagsSerializer(serializers.Serializer):
    id = serializers.CharField(read_only=True)
    name = serializers.CharField(read_only=True)
    flags = serializers.SerializerMethodField(read_only=True)

    def get_flags(self, instance):
        if self.context.get("active_flags_only"):
            return list(instance.flags.filter(status=FlagStatuses.ACTIVE).values("id", "name", "colour", "label"))
        else:
            return list(instance.flags.values("id", "name", "colour", "label"))
