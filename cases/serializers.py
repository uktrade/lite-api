from django.contrib.contenttypes.models import ContentType
from rest_framework import serializers

from applications.helpers import get_application_view_serializer
from applications.libraries.get_applications import get_application
from applications.serializers.advice import CaseAdviceSerializer
from audit_trail.models import Audit
from cases.enums import (
    CaseTypeTypeEnum,
    AdviceType,
    CaseDocumentState,
    CaseTypeSubTypeEnum,
    CaseTypeReferenceEnum,
    ECJUQueryType,
)
from cases.fields import CaseAssignmentRelatedSerializerField, HasOpenECJUQueriesRelatedField
from cases.libraries.get_flags import get_ordered_flags
from cases.models import (
    Case,
    CaseNote,
    CaseAssignment,
    CaseDocument,
    EcjuQuery,
    Advice,
    GoodCountryDecision,
    CaseType,
)
from conf.serializers import KeyValueChoiceField, PrimaryKeyRelatedSerializerField
from documents.libraries.process_document import process_document
from goodstype.models import GoodsType
from gov_users.serializers import GovUserSimpleSerializer, GovUserNotificationSerializer
from lite_content.lite_api import strings
from organisations.models import Organisation
from organisations.serializers import OrganisationCaseSerializer
from queries.serializers import QueryViewSerializer
from queues.models import Queue
from queues.serializers import CasesQueueViewSerializer
from static.countries.models import Country
from static.statuses.enums import CaseStatusEnum
from teams.serializers import TeamSerializer
from users.enums import UserStatuses
from users.models import BaseUser, GovUser, ExporterUser, GovNotification
from users.serializers import (
    BaseUserViewSerializer,
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


class CaseListSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    reference_code = serializers.CharField()
    case_type = PrimaryKeyRelatedSerializerField(queryset=CaseType.objects.all(), serializer=CaseTypeSerializer)
    assignments = CaseAssignmentRelatedSerializerField(source="case_assignments")
    status = serializers.SerializerMethodField()
    flags = serializers.SerializerMethodField()
    submitted_at = serializers.SerializerMethodField()
    sla_days = serializers.IntegerField()
    sla_remaining_days = serializers.IntegerField()
    has_open_ecju_queries = HasOpenECJUQueriesRelatedField(source="case_ecju_query")
    organisation = PrimaryKeyRelatedSerializerField(
        queryset=Organisation.objects.all(), serializer=OrganisationCaseSerializer
    )

    def __init__(self, *args, **kwargs):
        self.team = kwargs.pop("team", None)
        self.include_hidden = kwargs.pop("include_hidden", None)
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

    def get_status(self, instance):
        return {"key": instance.status.status, "value": CaseStatusEnum.get_text(instance.status.status)}


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
            "visible_to_exporter",
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
            "visible_to_exporter",
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


class EcjuQueryCreateSerializer(serializers.ModelSerializer):
    """
    Create specific serializer, which does not take a response as gov users don't respond to their own queries!
    """

    question = serializers.CharField(max_length=5000, allow_blank=False, allow_null=False)
    case = serializers.PrimaryKeyRelatedField(queryset=Case.objects.all())
    query_type = KeyValueChoiceField(choices=ECJUQueryType.choices)

    class Meta:
        model = EcjuQuery
        fields = (
            "id",
            "question",
            "case",
            "raised_by_user",
            "query_type",
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
        fields = ("case_officer",)
