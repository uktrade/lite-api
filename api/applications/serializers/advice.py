import logging
import uuid

from django.conf import settings
from api.staticdata.denial_reasons.serializers import DenialReasonSerializer
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from api.cases.enums import AdviceType
from api.cases.models import Advice, Case, CountersignAdvice
from api.core.serializers import PrimaryKeyRelatedSerializerField, KeyValueChoiceField
from api.flags.enums import FlagStatuses
from api.goods.models import Good
from api.applications.models import GoodOnApplication
from api.goodstype.models import GoodsType
from api.gov_users.serializers import (
    GovUserListSerializer,
    GovUserSimpleSerializer,
    GovUserViewSerializer,
)
from lite_content.lite_api import strings
from api.parties.enums import PartyType
from api.parties.models import Party
from api.staticdata.countries.models import Country
from api.staticdata.denial_reasons.models import DenialReason
from api.teams.models import Team
from api.teams.serializers import TeamReadOnlySerializer
from api.users.models import GovUser
from api.users.enums import UserStatuses


denial_reasons_logger = logging.getLogger(settings.DENIAL_REASONS_DELETION_LOGGER)


class GoodField(serializers.Field):
    def to_representation(self, instance):
        return str(instance.id)

    def to_internal_value(self, value):
        try:
            return Good.objects.get(pk=value)
        except Good.DoesNotExist:
            try:
                return GoodOnApplication.objects.get(pk=value).good
            except GoodOnApplication.DoesNotExist:
                return None


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

    good = GoodField()
    goods_type = serializers.UUIDField(source="goods_type_id")
    country = serializers.UUIDField(source="country_id")
    end_user = serializers.UUIDField(source="end_user_id")
    ultimate_end_user = serializers.UUIDField(source="ultimate_end_user_id")
    consignee = serializers.UUIDField(source="consignee_id")
    third_party = serializers.UUIDField(source="third_party_id")
    countersigned_by = PrimaryKeyRelatedSerializerField(
        queryset=GovUser.objects.all(), serializer=GovUserListSerializer
    )
    countersign_comments = serializers.CharField()
    # This field is used to differentiate Advices. Since we are implementing Licensing Unit notes, which replace refusal_reasons for LU ONLY
    # we need to keep track of this new note. If it's set to True, we know that it represents an Advice Refusal Note, rather than refusal_reasons, etc.
    # The other thing I was thinking about was whether a charfield could be a better way to distinguish the text type...
    # e.g. text_category=Choice("refusal_meeting_note", "refusal_reasons", "note", ...)
    # Maybe we could consider that down the line if we need to do more categorisation here.
    is_refusal_note = serializers.BooleanField()


class AdviceSearchViewSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    type = KeyValueChoiceField(choices=AdviceType.choices)
    denial_reasons = PrimaryKeyRelatedSerializerField(
        queryset=DenialReason.objects.all(), many=True, serializer=DenialReasonSerializer
    )
    user = PrimaryKeyRelatedSerializerField(
        queryset=GovUser.objects.all(),
        serializer=GovUserSimpleSerializer,
    )


class AdviceCreateSerializer(serializers.ModelSerializer):
    text = serializers.CharField(required=True, error_messages={"blank": strings.Advice.TEXT})
    note = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    type = KeyValueChoiceField(
        choices=AdviceType.choices, required=True, error_messages={"required": strings.Advice.TYPE}
    )
    level = serializers.CharField()
    proviso = serializers.CharField(required=False, allow_blank=True, allow_null=True)
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

    good = GoodField(required=False)
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
            if (
                self.initial_data[0].get("type") != AdviceType.REFUSE
                or self.initial_data[0].get("type") != AdviceType.NO_LICENCE_REQUIRED
            ):
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


class AdviceUpdateListSerializer(serializers.ListSerializer):
    def update(self, instance, validated_data):
        # Maps for id->instance and id->data item.
        advice_mapping = {advice.id: advice for advice in instance}
        data_mapping = {uuid.UUID(item["id"]): item for item in validated_data}

        ret = []
        for advice_id, data in data_mapping.items():
            advice = advice_mapping.get(advice_id)
            ret.append(self.child.update(advice, data))

        return ret


class AdviceUpdateSerializer(AdviceCreateSerializer):
    # https://www.django-rest-framework.org/api-guide/serializers/#customizing-multiple-update
    # You will need to add an explicit id field to the instance serializer.
    # The default implicitly-generated id field is marked as read_only.
    # This causes it to be removed on updates. Once you declare it explicitly,
    # it will be available in the list serializer's update method.
    id = serializers.CharField()

    class Meta:
        model = Advice
        list_serializer_class = AdviceUpdateListSerializer
        fields = (
            "id",
            "text",
            "note",
            "proviso",
            "type",
            "level",
            "denial_reasons",
            "footnote",
            "footnote_required",
            "user",
            "team",
            "good",
            "end_user",
            "ultimate_end_user",
            "consignee",
            "third_party",
            "country",
            "is_refusal_note",
        )


class CountersignAdviceListSerializer(serializers.ListSerializer):
    def update(self, instances, validated_data):
        instance_map = {index: instance for index, instance in enumerate(instances)}
        result = [self.child.update(instance_map[index], data) for index, data in enumerate(validated_data)]
        return result


class CountersignAdviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Advice
        fields = ("id", "countersigned_by", "countersign_comments")
        list_serializer_class = CountersignAdviceListSerializer


class CountersignAdviceWithDecisionListSerializer(serializers.ListSerializer):
    def update(self, instances, validated_data):
        instance_map = {index: instance for index, instance in enumerate(instances)}
        result = [self.child.update(instance_map[index], data) for index, data in enumerate(validated_data)]
        return result


class CountersignDecisionAdviceSerializer(serializers.ModelSerializer):
    countersigned_user = serializers.PrimaryKeyRelatedField(queryset=GovUser.objects.filter(status=UserStatuses.ACTIVE))
    case = serializers.PrimaryKeyRelatedField(queryset=Case.objects.all())
    advice = serializers.PrimaryKeyRelatedField(queryset=Advice.objects.all())

    class Meta:
        model = CountersignAdvice
        fields = ("id", "order", "outcome_accepted", "reasons", "countersigned_user", "case", "advice")
        list_serializer_class = CountersignAdviceWithDecisionListSerializer


class CountersignDecisionAdviceViewSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    valid = serializers.BooleanField()
    order = serializers.IntegerField()
    outcome_accepted = serializers.BooleanField()
    reasons = serializers.CharField()
    countersigned_user = GovUserViewSerializer()
    advice = AdviceViewSerializer()


class CountryWithFlagsSerializer(serializers.Serializer):
    id = serializers.CharField(read_only=True)
    name = serializers.CharField(read_only=True)
    flags = serializers.SerializerMethodField(read_only=True)

    def get_flags(self, instance):
        if self.context.get("active_flags_only"):
            return list(instance.flags.filter(status=FlagStatuses.ACTIVE).values("id", "name", "colour", "label"))
        else:
            return list(instance.flags.values("id", "name", "colour", "label"))
