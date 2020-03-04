from django.contrib.contenttypes.models import ContentType
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from applications.helpers import get_application_view_serializer
from applications.libraries.get_applications import get_application
from audit_trail.models import Audit
from cases.enums import (
    CaseTypeTypeEnum,
    AdviceType,
    CaseDocumentState,
    CaseTypeSubTypeEnum,
    CaseTypeReferenceEnum,
)
from cases.libraries.get_destination import get_ordered_flags
from cases.models import (
    Case,
    CaseNote,
    CaseAssignment,
    CaseDocument,
    Advice,
    EcjuQuery,
    TeamAdvice,
    FinalAdvice,
    GoodCountryDecision,
    CaseType,
)
from conf.helpers import convert_queryset_to_str, ensure_x_items_not_none
from conf.serializers import KeyValueChoiceField, PrimaryKeyRelatedSerializerField
from documents.libraries.process_document import process_document
from goods.models import Good
from goodstype.models import GoodsType
from gov_users.serializers import GovUserSimpleSerializer, GovUserNotificationSerializer
from lite_content.lite_api import strings
from parties.enums import PartyType
from parties.models import Party
from queries.serializers import QueryViewSerializer
from queues.models import Queue
from static.countries.models import Country
from static.denial_reasons.models import DenialReason
from static.statuses.enums import CaseStatusEnum
from teams.models import Team
from teams.serializers import TeamSerializer
from users.enums import UserStatuses
from users.models import BaseUser, GovUser, ExporterUser, GovNotification
from users.serializers import (
    BaseUserViewSerializer,
    GovUserViewSerializer,
    ExporterUserViewSerializer,
)


class CaseTypeSerializer(serializers.ModelSerializer):
    reference = KeyValueChoiceField(choices=CaseTypeReferenceEnum.choices)
    type = KeyValueChoiceField(choices=CaseTypeTypeEnum.choices)
    sub_type = KeyValueChoiceField(choices=CaseTypeSubTypeEnum.choices)

    class Meta:
        model = CaseType
        fields = (
            "id",
            "reference",
            "type",
            "sub_type",
        )


class CaseSerializer(serializers.ModelSerializer):
    """
    Serializes cases
    """

    case_type = PrimaryKeyRelatedSerializerField(queryset=CaseType.objects.all(), serializer=CaseTypeSerializer)
    application = serializers.SerializerMethodField()
    query = QueryViewSerializer(read_only=True)

    class Meta:
        model = Case
        fields = (
            "id",
            "case_type",
            "application",
            "query",
        )

    def get_application(self, instance):
        # The case has a reference to a BaseApplication but
        # we need the full details of the application it points to
        if instance.type in [CaseTypeTypeEnum.APPLICATION]:
            application = get_application(instance.id)
            serializer = get_application_view_serializer(application)
            return serializer(application).data

    def to_representation(self, value):
        """
        Only show 'application' if it has an application inside,
        and only show 'query' if it has a CLC query inside
        """
        repr_dict = super(CaseSerializer, self).to_representation(value)
        if not repr_dict["application"]:
            del repr_dict["application"]
        if not repr_dict["query"]:
            del repr_dict["query"]
        return repr_dict


class CaseListSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    reference_code = serializers.CharField()
    queues = serializers.PrimaryKeyRelatedField(many=True, queryset=Queue.objects.all())
    case_type = PrimaryKeyRelatedSerializerField(queryset=CaseType.objects.all(), serializer=CaseTypeSerializer)
    queue_names = serializers.SerializerMethodField()
    organisation = serializers.SerializerMethodField()
    users = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    query = QueryViewSerializer()
    flags = serializers.SerializerMethodField()
    submitted_at = serializers.SerializerMethodField()
    sla_days = serializers.IntegerField()
    sla_remaining_days = serializers.IntegerField()

    def __init__(self, *args, **kwargs):
        self.team = kwargs.pop("team", None)
        super().__init__(*args, **kwargs)

    def get_flags(self, instance):
        """
        Gets flags for a case and returns in sorted order by team.
        """
        return get_ordered_flags(instance, self.team)

    def get_submitted_at(self, instance):
        # Return the DateTime value manually as otherwise
        # it'll return a string representation which isn't suitable for filtering
        return instance.submitted_at

    def get_queue_names(self, instance):
        return list(instance.queues.values_list("name", flat=True))

    def get_organisation(self, instance):
        return instance.organisation.name

    def get_status(self, instance):
        return {"key": instance.status.status, "value": CaseStatusEnum.get_text(instance.status.status)}

    def get_users(self, instance):
        return instance.get_users(queue=self.context["queue_id"] if not self.context["is_system_queue"] else None)


class CaseCopyOfSerializer(serializers.ModelSerializer):
    class Meta:
        model = Case
        fields = (
            "id",
            "reference_code",
        )


class CaseDetailSerializer(CaseSerializer):
    queues = serializers.PrimaryKeyRelatedField(many=True, queryset=Queue.objects.all())
    queue_names = serializers.SerializerMethodField()
    users = serializers.SerializerMethodField()
    has_advice = serializers.SerializerMethodField()
    flags = serializers.SerializerMethodField()
    query = QueryViewSerializer(read_only=True)
    application = serializers.SerializerMethodField()
    all_flags = serializers.SerializerMethodField()
    case_officer = GovUserSimpleSerializer(read_only=True)
    copy_of = serializers.SerializerMethodField()
    audit_notification = serializers.SerializerMethodField()
    sla_days = serializers.IntegerField()
    sla_remaining_days = serializers.IntegerField()

    class Meta:
        model = Case
        fields = (
            "id",
            "case_type",
            "flags",
            "queues",
            "queue_names",
            "users",
            "application",
            "query",
            "has_advice",
            "all_flags",
            "case_officer",
            "audit_notification",
            "reference_code",
            "copy_of",
            "sla_days",
            "sla_remaining_days",
        )

    def __init__(self, *args, **kwargs):
        self.team = kwargs.pop("team", None)
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

    def get_application(self, instance):
        # The case has a reference to a BaseApplication but
        # we need the full details of the application it points to
        if instance.case_type.type == CaseTypeTypeEnum.APPLICATION:
            application = get_application(instance.id)
            serializer = get_application_view_serializer(application)
            return serializer(application).data

    def get_flags(self, instance):
        return list(instance.flags.all().values("id", "name"))

    def get_queue_names(self, instance):
        return list(instance.queues.values_list("name", flat=True))

    def get_users(self, instance):
        return instance.get_users()

    def get_has_advice(self, instance):
        has_advice = {"team": False, "my_team": False, "final": False}

        if TeamAdvice.objects.filter(case=instance).first():
            has_advice["team"] = True

        if FinalAdvice.objects.filter(case=instance).first():
            has_advice["final"] = True

        try:
            team_advice = TeamAdvice.objects.filter(case=instance, team=self.team).values_list("id", flat=True)

            if team_advice.exists():
                has_advice["my_team"] = True

            if Advice.objects.filter(case=instance, user=self.user).exclude(id__in=team_advice).exists():
                has_advice["my_user"] = True
        except AttributeError:
            pass
        return has_advice

    def get_all_flags(self, instance):
        """
        Gets flags for a case and returns in sorted order by team.
        """
        return get_ordered_flags(instance, self.team)

    def get_audit_notification(self, instance):
        content_type = ContentType.objects.get_for_model(Audit)
        queryset = GovNotification.objects.filter(user=self.user, content_type=content_type, case=instance)

        if queryset.exists():
            notification = queryset.first()
            return GovUserNotificationSerializer(notification).data

        return None

    def get_copy_of(self, instance):
        if instance.copy_of and instance.copy_of.status.status != CaseStatusEnum.DRAFT:
            return CaseCopyOfSerializer(instance.copy_of).data


class CaseNoteSerializer(serializers.ModelSerializer):
    """
    Serializes case notes
    """

    text = serializers.CharField(
        min_length=2,
        max_length=2200,
        error_messages={
            "blank": strings.Cases.CaseNotes.BLANK,
            "min_length": strings.Cases.CaseNotes.MIN_LENGTH,
            "max_length": strings.Cases.CaseNotes.MAX_LENGTH,
        },
    )
    case = serializers.PrimaryKeyRelatedField(queryset=Case.objects.all())
    user = PrimaryKeyRelatedSerializerField(queryset=BaseUser.objects.all(), serializer=BaseUserViewSerializer)
    created_at = serializers.DateTimeField(read_only=True)
    is_visible_to_exporter = serializers.BooleanField(default=False)

    class Meta:
        model = CaseNote
        fields = "__all__"


class CaseAssignmentSerializer(serializers.ModelSerializer):
    users = GovUserSimpleSerializer(many=True)

    class Meta:
        model = CaseAssignment
        fields = (
            "case",
            "users",
        )


class CaseDocumentCreateSerializer(serializers.ModelSerializer):
    case = serializers.PrimaryKeyRelatedField(queryset=Case.objects.all())
    user = serializers.PrimaryKeyRelatedField(queryset=GovUser.objects.all())

    class Meta:
        model = CaseDocument
        fields = (
            "name",
            "s3_key",
            "user",
            "size",
            "case",
            "description",
        )

    def create(self, validated_data):
        case_document = super(CaseDocumentCreateSerializer, self).create(validated_data)
        case_document.save()
        process_document(case_document)
        return case_document


class CaseDocumentViewSerializer(serializers.ModelSerializer):
    created_at = serializers.DateTimeField(read_only=True)
    case = serializers.PrimaryKeyRelatedField(queryset=Case.objects.all())
    user = GovUserSimpleSerializer()
    metadata_id = serializers.SerializerMethodField()
    type = KeyValueChoiceField(choices=CaseDocumentState.choices)

    def get_metadata_id(self, instance):
        return instance.id if instance.safe else "File not ready"

    class Meta:
        model = CaseDocument
        fields = (
            "id",
            "name",
            "type",
            "metadata_id",
            "user",
            "size",
            "case",
            "created_at",
            "safe",
            "description",
        )


class CaseAdviceSerializer(serializers.ModelSerializer):
    case = serializers.PrimaryKeyRelatedField(queryset=Case.objects.all())
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

    # Optional fields
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

    class Meta:
        model = Advice
        fields = (
            "case",
            "user",
            "text",
            "note",
            "type",
            "proviso",
            "denial_reasons",
            "good",
            "goods_type",
            "country",
            "end_user",
            "ultimate_end_user",
            "created_at",
            "consignee",
            "third_party",
        )

    def validate_denial_reasons(self, value):
        """
        Check that the denial reasons are set if type is REFUSE
        """
        for data in self.initial_data:
            if data["type"] == AdviceType.REFUSE and not data["denial_reasons"]:
                raise serializers.ValidationError("Select at least one denial reason")

        return value

    def validate_proviso(self, value):
        """
        Check that the proviso is set if type is REFUSE
        """
        for data in self.initial_data:
            if data["type"] == AdviceType.PROVISO and not data["proviso"]:
                raise ValidationError("Provide a proviso")

        return value

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
                    raise ValidationError("Only one item (such as an end_user) can be given at a time")

    def to_representation(self, instance):
        repr_dict = super(CaseAdviceSerializer, self).to_representation(instance)
        if instance.type != AdviceType.CONFLICTING:
            if instance.type == AdviceType.PROVISO:
                repr_dict["proviso"] = instance.proviso
            else:
                del repr_dict["proviso"]

            if instance.type == AdviceType.REFUSE:
                repr_dict["denial_reasons"] = convert_queryset_to_str(
                    instance.denial_reasons.values_list("id", flat=True)
                )
            else:
                del repr_dict["denial_reasons"]

        return repr_dict


class CaseTeamAdviceSerializer(CaseAdviceSerializer):
    team = PrimaryKeyRelatedSerializerField(queryset=Team.objects.all(), serializer=TeamSerializer)

    class Meta:
        model = TeamAdvice
        fields = "__all__"


class CaseFinalAdviceSerializer(CaseAdviceSerializer):
    class Meta:
        model = FinalAdvice
        fields = "__all__"


class EcjuQueryGovSerializer(serializers.ModelSerializer):
    raised_by_user_name = serializers.SerializerMethodField()
    responded_by_user_name = serializers.SerializerMethodField()

    class Meta:
        model = EcjuQuery
        fields = (
            "id",
            "question",
            "response",
            "case",
            "responded_by_user_name",
            "raised_by_user_name",
            "created_at",
            "responded_at",
        )

    def get_raised_by_user_name(self, instance):
        return instance.raised_by_user.get_full_name()

    def get_responded_by_user_name(self, instance):
        if instance.responded_by_user:
            return instance.responded_by_user.get_full_name()


class EcjuQueryExporterSerializer(serializers.ModelSerializer):
    team = serializers.SerializerMethodField()
    responded_by_user = PrimaryKeyRelatedSerializerField(
        queryset=ExporterUser.objects.all(), serializer=ExporterUserViewSerializer
    )
    response = serializers.CharField(max_length=2200, allow_blank=False, allow_null=False)

    def get_team(self, instance):
        return TeamSerializer(instance.raised_by_user.team).data

    class Meta:
        model = EcjuQuery
        fields = (
            "id",
            "question",
            "response",
            "case",
            "responded_by_user",
            "team",
            "created_at",
            "responded_at",
        )


class EcjuQueryCreateSerializer(serializers.ModelSerializer):
    """
    Create specific serializer, which does not take a response as gov users don't respond to their own queries!
    """

    question = serializers.CharField(max_length=5000, allow_blank=False, allow_null=False)
    case = serializers.PrimaryKeyRelatedField(queryset=Case.objects.all())

    class Meta:
        model = EcjuQuery
        fields = (
            "id",
            "question",
            "case",
            "raised_by_user",
        )


class GoodCountryDecisionSerializer(serializers.ModelSerializer):
    case = serializers.PrimaryKeyRelatedField(queryset=Case.objects.all())
    good = serializers.PrimaryKeyRelatedField(queryset=GoodsType.objects.all())
    country = serializers.PrimaryKeyRelatedField(queryset=Country.objects.all())
    decision = KeyValueChoiceField(choices=AdviceType.choices)

    class Meta:
        model = GoodCountryDecision
        fields = "__all__"


class CaseOfficerUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for assigning and removing case officers from a case.
    """

    case_officer = serializers.PrimaryKeyRelatedField(
        queryset=GovUser.objects.exclude(status=UserStatuses.DEACTIVATED).all(), allow_null=True
    )

    class Meta:
        model = Case
        fields = (
            "id",
            "case_officer",
        )
