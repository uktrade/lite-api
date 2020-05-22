from django.contrib.contenttypes.models import ContentType
from rest_framework import serializers

from applications.helpers import get_application_view_serializer
from applications.libraries.get_applications import get_application
from applications.serializers.advice import CaseAdviceSerializer
from audit_trail.models import Audit
from cases.enums import CaseTypeTypeEnum, CaseDocumentState, AdviceType, ECJUQueryType
from cases.libraries.get_flags import get_ordered_flags
from cases.models import CaseType, Case, Advice, CaseNote, CaseDocument, CaseAssignment, EcjuQuery, GoodCountryDecision
from cases.serializers.list import CaseTypeSerializer
from conf.serializers import PrimaryKeyRelatedSerializerField, KeyValueChoiceField
from goodstype.models import GoodsType
from gov_users.serializers import GovUserSimpleSerializer, GovUserNotificationSerializer, CaseOfficerReadOnlySerializer
from lite_content.lite_api import strings
from queries.serializers import QueryViewSerializer
from queues.models import Queue
from queues.serializers import CasesQueueViewSerializer
from static.countries.models import Country
from static.statuses.enums import CaseStatusEnum
from teams.serializers import TeamSerializer
from users.models import GovNotification, BaseUser, GovUser, ExporterUser
from users.serializers import BaseUserViewSerializer, ExporterUserViewSerializer


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


class CaseDetailSerializerOld(CaseSerializer):
    queues = serializers.PrimaryKeyRelatedField(many=True, queryset=Queue.objects.all())
    queue_names = serializers.SerializerMethodField()
    assigned_users = serializers.SerializerMethodField()
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
    advice = CaseAdviceSerializer(many=True)

    class Meta:
        model = Case
        fields = (
            "id",
            "case_type",
            "flags",
            "queues",
            "queue_names",
            "assigned_users",
            "application",
            "query",
            "has_advice",
            "advice",
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
        return list(instance.flags.all().values("id", "name", "colour", "label", "priority"))

    def get_queue_names(self, instance):
        return list(instance.queues.values_list("name", flat=True))

    def get_assigned_users(self, instance):
        return instance.get_users()

    def get_has_advice(self, instance):
        has_advice = {"user": False, "my_user": False, "team": False, "my_team": False, "final": False}

        team_advice = Advice.objects.filter(case=instance).values_list("id", flat=True)
        if team_advice.exists():
            has_advice["team"] = True

        final_advice = Advice.objects.filter(case=instance).values_list("id", flat=True)
        if final_advice.exists():
            has_advice["final"] = True

        if Advice.objects.filter(case=instance).exclude(id__in=team_advice.union(final_advice)).exists():
            has_advice["user"] = True

        my_team_advice = Advice.objects.filter(case=instance, team=self.team).values_list("id", flat=True)
        if my_team_advice.exists():
            has_advice["my_team"] = True

        if Advice.objects.filter(case=instance, user=self.user).exclude(id__in=my_team_advice).exists():
            has_advice["my_user"] = True

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


class CaseDetailSerializer(serializers.Serializer):
    # Key properties
    id = serializers.UUIDField()
    all_flags = serializers.SerializerMethodField()
    case_officer = CaseOfficerReadOnlySerializer()
    assigned_users = serializers.SerializerMethodField()

    def __init__(self, *args, **kwargs):
        self.team = kwargs.pop("team", None)
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

    def get_all_flags(self, instance):
        """
        Gets flags for a case and returns in sorted order by team.
        """
        return get_ordered_flags(instance, self.team)

    def get_assigned_users(self, instance):
        # TODO Improve
        return instance.get_users()


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
            "visible_to_exporter",
        )


class CaseAssignmentSerializer(serializers.ModelSerializer):
    user = GovUserSimpleSerializer()

    class Meta:
        model = CaseAssignment
        fields = (
            "case",
            "user",
        )


class QueueCaseAssignmentUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = GovUser
        fields = (
            "id",
            "first_name",
            "last_name",
            "email",
        )


class QueueCaseAssignmentSerializer(serializers.ModelSerializer):
    user = QueueCaseAssignmentUserSerializer()
    queue = CasesQueueViewSerializer()

    class Meta:
        model = CaseAssignment
        fields = (
            "user",
            "queue",
        )


class CaseCopyOfSerializer(serializers.ModelSerializer):
    class Meta:
        model = Case
        fields = (
            "id",
            "reference_code",
        )


class SimpleAdviceSerializer(serializers.ModelSerializer):
    type = KeyValueChoiceField(choices=AdviceType.choices)

    class Meta:
        model = Advice
        fields = ("type", "text", "proviso")
        read_only_fields = fields


class EcjuQueryGovSerializer(serializers.ModelSerializer):
    raised_by_user_name = serializers.SerializerMethodField()
    responded_by_user_name = serializers.SerializerMethodField()
    query_type = KeyValueChoiceField(choices=ECJUQueryType.choices, required=False)

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
            "query_type",
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


class GoodCountryDecisionSerializer(serializers.ModelSerializer):
    case = serializers.PrimaryKeyRelatedField(queryset=Case.objects.all())
    good = serializers.PrimaryKeyRelatedField(queryset=GoodsType.objects.all())
    country = serializers.PrimaryKeyRelatedField(queryset=Country.objects.all())
    decision = KeyValueChoiceField(choices=AdviceType.choices)

    class Meta:
        model = GoodCountryDecision
        fields = "__all__"
