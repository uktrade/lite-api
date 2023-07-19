from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.utils import timezone

from api.applications.mixins.serializers import PartiesSerializerMixin
from api.cases.service import retrieve_latest_activity
from rest_framework import serializers

from api.applications.libraries.get_applications import get_application
from api.applications.serializers.advice import AdviceViewSerializer, CountersignDecisionAdviceViewSerializer
from api.applications.models import BaseApplication
from api.audit_trail.models import Audit
from api.cases.enums import (
    CaseTypeTypeEnum,
    AdviceType,
    CaseDocumentState,
    CaseTypeSubTypeEnum,
    CaseTypeReferenceEnum,
    ECJUQueryType,
)
from api.cases.libraries.get_flags import get_ordered_flags
from api.cases.models import (
    Case,
    CaseNote,
    CaseNoteMentions,
    CaseAssignment,
    CaseAssignmentSLA,
    CaseDocument,
    CaseQueue,
    EcjuQuery,
    EcjuQueryDocument,
    Advice,
    GoodCountryDecision,
    CaseType,
    CaseReviewDate,
)
from api.compliance.models import ComplianceSiteCase, ComplianceVisitCase
from api.compliance.serializers.ComplianceSiteCaseSerializers import ComplianceSiteViewSerializer
from api.compliance.serializers.ComplianceVisitCaseSerializers import ComplianceVisitSerializer
from api.core.serializers import KeyValueChoiceField, PrimaryKeyRelatedSerializerField
from api.documents.libraries.process_document import process_document
from api.goodstype.models import GoodsType
from api.gov_users.serializers import GovUserSimpleSerializer
from api.licences.helpers import get_open_general_export_licence_case
from api.queries.serializers import QueryViewSerializer
from api.queues.models import Queue
from api.queues.serializers import QueueListSerializer
from api.staticdata.countries.models import Country
from api.staticdata.statuses.enums import CaseStatusEnum
from api.teams.models import Team
from api.teams.serializers import TeamSerializer
from api.users.enums import UserStatuses
from api.users.models import BaseUser, GovUser, GovNotification, ExporterUser
from api.users.serializers import (
    BaseUserViewSerializer,
    GovUserViewSerializer,
    ExporterUserViewSerializer,
    ExporterUserSimpleSerializer,
)
from api.queues.constants import ALL_CASES_QUEUE_ID
from lite_content.lite_api import strings


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


class CaseTypeReferenceListSerializer(serializers.Serializer):
    reference = KeyValueChoiceField(choices=CaseTypeReferenceEnum.choices)


class CaseAssignmentSerializer(serializers.ModelSerializer):
    user = GovUserSimpleSerializer()

    class Meta:
        model = CaseAssignment
        fields = (
            "case",
            "user",
            "id",
            "queue",
        )


class CaseAssignmentSLASerializer(serializers.ModelSerializer):
    class Meta:
        model = CaseAssignmentSLA
        fields = "__all__"


class CaseQueueSerializer(serializers.ModelSerializer):
    class Meta:
        model = CaseQueue
        fields = "__all__"


class QueueCaseAssignmentUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = GovUser
        fields = (
            "id",
            "first_name",
            "last_name",
            "email",
        )


class CaseListSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    reference_code = serializers.CharField()
    case_type = PrimaryKeyRelatedSerializerField(queryset=CaseType.objects.all(), serializer=CaseTypeSerializer)
    queues = serializers.SerializerMethodField()
    assignments = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    submitted_at = serializers.SerializerMethodField()
    sla_days = serializers.IntegerField()
    sla_remaining_days = serializers.IntegerField()
    next_review_date = serializers.DateField()
    has_open_queries = serializers.BooleanField()
    case_officer = serializers.SerializerMethodField()
    intended_end_use = serializers.SerializerMethodField()
    endusers = serializers.SerializerMethodField()

    def __init__(self, *args, **kwargs):
        self.team = kwargs.pop("team", None)
        self.include_hidden = kwargs.pop("include_hidden", None)
        super().__init__(*args, **kwargs)

    def get_queues(self, instance):
        return QueueListSerializer(instance.queues.all(), many=True).data

    def get_assignments(self, instance):
        return_value = {}

        for assignment in instance.case_assignments.all():
            user_id = str(assignment.user.pk)
            if user_id not in return_value:
                return_value[user_id] = {}
            return_value[user_id]["first_name"] = assignment.user.first_name
            return_value[user_id]["last_name"] = assignment.user.last_name
            return_value[user_id]["email"] = assignment.user.email
            return_value[user_id]["team_name"] = assignment.user.team.name
            return_value[user_id]["team_id"] = str(assignment.user.team.id)
            if "queues" not in return_value[user_id]:
                return_value[user_id]["queues"] = []
            return_value[user_id]["queues"].append({"name": assignment.queue.name, "id": str(assignment.queue.id)})

        return return_value

    def get_submitted_at(self, instance):
        # Return the DateTime value manually as otherwise
        # it'll return a string representation which isn't suitable for filtering
        return instance.submitted_at

    def get_status(self, instance):
        return {"key": instance.status.status, "value": CaseStatusEnum.get_text(instance.status.status)}

    def get_case_officer(self, instance):
        if instance.case_officer:
            return {
                "first_name": instance.case_officer.first_name,
                "last_name": instance.case_officer.last_name,
                "email": instance.case_officer.email,
            }

    def get_intended_end_use(self, instance):
        try:
            return instance.baseapplication.intended_end_use or ""
        except BaseApplication.DoesNotExist:
            return ""

    def get_endusers(self, instance):
        parties = (
            instance.baseapplication.parties.filter(
                party__type__in=["end_user", "ultimate_end_user"], deleted_at__isnull=True
            )
            .select_related("party")
            .prefetch_related(
                "party__name",
                "party__type",
            )
            .values("party__name", "party__type")
        )

        return [{"name": party["party__name"], "type": party["party__type"]} for party in parties]


class GoodOnApplicationSummarySerializer(serializers.Serializer):
    name = serializers.CharField()
    cles = serializers.SerializerMethodField()
    report_summary_subject = serializers.CharField(source="report_summary_subject.name", default=None)
    report_summary_prefix = serializers.CharField(source="report_summary_prefix.name", default=None)
    quantity = serializers.DecimalField(max_digits=None, decimal_places=2)
    value = serializers.DecimalField(max_digits=None, decimal_places=2)
    regimes = serializers.SerializerMethodField()

    def get_cles(self, instance):
        return [cle.rating for cle in instance.control_list_entries.all()]

    def get_regimes(self, instance):
        return [regime_entry.name for regime_entry in instance.regime_entries.all()]


class DenialMatchOnApplicationSummarySerializer(serializers.Serializer):
    """
    Serializer for a DenialMatchOnApplication and fields from the related Denial
    record.
    """

    name = serializers.CharField(source="denial.name")
    reference = serializers.CharField(source="denial.reference")
    category = serializers.CharField()
    address = serializers.CharField(source="denial.address")


class ECJUQuerySummarySerializer(serializers.Serializer):
    question = serializers.CharField()
    response = serializers.CharField()
    raised_by_user = serializers.SerializerMethodField()
    responded_by_user = serializers.SerializerMethodField()
    query_type = serializers.CharField()

    def _user_name(self, user):
        if not user:
            return None
        return f"{user.first_name} {user.last_name}" if (user.first_name and user.last_name) else user.email

    def get_raised_by_user(self, instance):
        return self._user_name(instance.raised_by_user)

    def get_responded_by_user(self, instance):
        return self._user_name(instance.responded_by_user)


class CaseCopyOfSerializer(serializers.ModelSerializer):
    class Meta:
        model = Case
        fields = (
            "id",
            "reference_code",
        )


class CaseDetailSerializer(serializers.ModelSerializer):
    queues = serializers.PrimaryKeyRelatedField(many=True, queryset=Queue.objects.all())
    queue_names = serializers.SerializerMethodField()
    queue_details = serializers.SerializerMethodField()
    assigned_users = serializers.SerializerMethodField()
    has_advice = serializers.SerializerMethodField()
    flags = serializers.SerializerMethodField()
    all_flags = serializers.SerializerMethodField()
    case_officer = GovUserSimpleSerializer(read_only=True)
    copy_of = serializers.SerializerMethodField()
    audit_notification = serializers.SerializerMethodField()
    sla_days = serializers.IntegerField()
    sla_remaining_days = serializers.IntegerField()
    advice = AdviceViewSerializer(many=True)
    countersign_advice = CountersignDecisionAdviceViewSerializer(many=True)
    data = serializers.SerializerMethodField()
    latest_activity = serializers.SerializerMethodField()
    case_type = PrimaryKeyRelatedSerializerField(queryset=CaseType.objects.all(), serializer=CaseTypeSerializer)
    next_review_date = serializers.SerializerMethodField()

    class Meta:
        model = Case
        fields = (
            "id",
            "case_type",
            "submitted_at",
            "flags",
            "queues",
            "queue_names",
            "queue_details",
            "assigned_users",
            "has_advice",
            "advice",
            "countersign_advice",
            "all_flags",
            "case_officer",
            "audit_notification",
            "reference_code",
            "copy_of",
            "sla_days",
            "sla_remaining_days",
            "data",
            "next_review_date",
            "latest_activity",
        )

    def __init__(self, *args, **kwargs):
        self.team = kwargs.pop("team", None)
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

    def get_data(self, instance):
        from api.licences.serializers.open_general_licences import OpenGeneralLicenceCaseSerializer
        from api.applications.helpers import get_application_view_serializer

        if instance.case_type.type == CaseTypeTypeEnum.REGISTRATION:
            return OpenGeneralLicenceCaseSerializer(get_open_general_export_licence_case(instance.id)).data
        elif instance.case_type.type == CaseTypeTypeEnum.APPLICATION:
            application = get_application(instance.id)
            serializer = get_application_view_serializer(application)
            return serializer(application).data
        elif instance.case_type.type == CaseTypeTypeEnum.QUERY:
            return QueryViewSerializer(instance.query, read_only=True).data
        elif instance.case_type.sub_type == CaseTypeSubTypeEnum.COMP_SITE:
            compliance = ComplianceSiteCase.objects.get(id=instance.id)
            return ComplianceSiteViewSerializer(compliance, context={"team": self.team}).data
        elif instance.case_type.sub_type == CaseTypeSubTypeEnum.COMP_VISIT:
            compliance = ComplianceVisitCase.objects.get(id=instance.id)
            return ComplianceVisitSerializer(compliance).data

    def get_flags(self, instance):
        return list(instance.flags.values("id", "name", "colour", "label", "priority", "alias"))

    def get_queue_names(self, instance):
        return list(instance.queues.values_list("name", flat=True))

    def get_queue_details(self, instance):
        # This should supersede queue/queue_names to make payload and DB query more efficient
        details = list(instance.queues.values("id", "name", "alias"))
        qs = CaseQueue.objects.filter(
            case_id=instance.id, queue_id__in=list(instance.queues.values_list("id", flat=True))
        )
        queue_map = {case_queue.queue_id: case_queue for case_queue in qs}
        for detail in details:
            case_queue = queue_map[detail["id"]]
            detail["joined_queue_at"] = case_queue.created_at
        return details

    def get_assigned_users(self, instance):
        return instance.get_assigned_users()

    def get_has_advice(self, instance):
        has_advice = {"user": False, "my_user": False, "team": False, "my_team": False, "final": False}

        team_advice = instance.advice.all()
        if team_advice.exists():
            has_advice["team"] = True

        final_advice = instance.advice.all()
        if final_advice.exists():
            has_advice["final"] = True

        my_team_advice = instance.advice.filter(team=self.team).values_list("id", flat=True)
        if my_team_advice.exists():
            has_advice["my_team"] = True

        if instance.advice.filter(user=self.user).exclude(id__in=my_team_advice).exists():
            has_advice["my_user"] = True

        return has_advice

    def get_latest_activity(self, instance):
        return retrieve_latest_activity(instance)

    def get_all_flags(self, instance):
        """
        Gets distinct flags for a case and returns in sorted order by team.
        """
        return get_ordered_flags(instance, self.team, distinct=True)

    def get_audit_notification(self, instance):
        content_type = ContentType.objects.get_for_model(Audit)
        queryset = GovNotification.objects.filter(user_id=self.user.pk, content_type=content_type, case=instance)

        if queryset.exists():
            return {"audit_id": queryset.first().object_id}

    def get_copy_of(self, instance):
        if instance.copy_of and instance.copy_of.status.status != CaseStatusEnum.DRAFT:
            return CaseCopyOfSerializer(instance.copy_of).data

    def get_next_review_date(self, instance):
        try:
            return instance.case_review_date.get(case_id=instance.id, team_id=self.team.id).next_review_date
        except CaseReviewDate.DoesNotExist:
            pass


class CaseNoteMentionsListSerializer(serializers.ListSerializer):
    def update(self, instances, validated_data):
        instance_map = {index: instance for index, instance in enumerate(instances)}
        result = [self.child.update(instance_map[index], data) for index, data in enumerate(validated_data)]
        return result

    def get_user_mention_names(self):
        names = []
        for m in self.data:
            name = (
                m["user"]["first_name"] + " " + m["user"]["last_name"]
                if m["user"]["first_name"]
                else m["user"]["email"]
            )
            team = m["user"].get("team", {}).get("name", "")
            names.append(f"{name} ({team})")
        return names


class CaseNoteMentionsSerializer(serializers.ModelSerializer):
    """
    Serializes case notes mentions
    """

    user = PrimaryKeyRelatedSerializerField(
        queryset=GovUser.objects.all(), serializer=GovUserViewSerializer, required=False
    )
    case_note_user = PrimaryKeyRelatedSerializerField(
        queryset=BaseUser.objects.all(), source="case_note.user", serializer=BaseUserViewSerializer, required=False
    )
    is_urgent = serializers.BooleanField(source="case_note.is_urgent", required=False)
    case_note_text = serializers.CharField(source="case_note.text", required=False)
    reference_code = serializers.CharField(source="case_note.case.reference_code", required=False, read_only=True)
    case_id = serializers.UUIDField(source="case_note.case.id", required=False, read_only=True)
    case_queue_id = serializers.SerializerMethodField()

    def get_case_queue_id(self, instance):
        # Check that the case's queue is still within the users team queue else fallback to all cases queue
        for case_queue in instance.case_note.case.queues.all():
            if case_queue in instance.user.team.queue_set.all():
                return case_queue.id
        return ALL_CASES_QUEUE_ID

    class Meta:
        model = CaseNoteMentions
        list_serializer_class = CaseNoteMentionsListSerializer
        fields = (
            "id",
            "case_note",
            "team",
            "is_accessed",
            "user",
            "created_at",
            "case_note_user",
            "is_urgent",
            "case_note_text",
            "reference_code",
            "case_queue_id",
            "case_id",
        )


class CaseNoteSerializer(serializers.ModelSerializer):
    """
    Serializes case notes
    """

    text = serializers.CharField(
        error_messages={
            "blank": strings.Cases.CaseNotes.BLANK,
        },
    )
    case = serializers.PrimaryKeyRelatedField(queryset=Case.objects.all())
    user = PrimaryKeyRelatedSerializerField(queryset=BaseUser.objects.all(), serializer=BaseUserViewSerializer)
    created_at = serializers.DateTimeField(read_only=True)
    is_visible_to_exporter = serializers.BooleanField(default=False)
    is_urgent = serializers.BooleanField(default=False)

    class Meta:
        model = CaseNote
        fields = "__all__"

    def create(self, validated_data):
        casenote = super(CaseNoteSerializer, self).create(validated_data)
        casenote.save()
        return casenote


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


class AdviceSerializer(serializers.ModelSerializer):
    type = KeyValueChoiceField(choices=AdviceType.choices)

    class Meta:
        model = Advice
        fields = "__all__"


class EcjuQueryGovSerializer(serializers.ModelSerializer):
    raised_by_user_name = serializers.SerializerMethodField()
    responded_by_user_name = serializers.SerializerMethodField()
    query_type = KeyValueChoiceField(choices=ECJUQueryType.choices, required=False)
    documents = serializers.SerializerMethodField()

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
            "documents",
        )

    def get_raised_by_user_name(self, instance):
        return instance.raised_by_user.baseuser_ptr.get_full_name()

    def get_responded_by_user_name(self, instance):
        if instance.responded_by_user:
            return instance.responded_by_user.baseuser_ptr.get_full_name()

    def get_documents(self, instance):
        documents = EcjuQueryDocument.objects.filter(query=instance)
        return SimpleEcjuQueryDocumentViewSerializer(documents, many=True).data


class EcjuQueryExporterViewSerializer(serializers.ModelSerializer):
    team = serializers.SerializerMethodField()
    responded_by_user = serializers.SerializerMethodField()
    response = serializers.CharField(max_length=2200, allow_blank=False, allow_null=False)
    documents = serializers.SerializerMethodField()

    def get_team(self, instance):
        # If the team is not available, use the user's current team.
        team = instance.team if instance.team else instance.raised_by_user.team
        return TeamSerializer(team).data

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
            "documents",
        )

    def get_responded_by_user(self, instance):
        if instance.responded_by_user:
            return {
                "id": instance.responded_by_user.pk,
                "name": instance.responded_by_user.baseuser_ptr.get_full_name(),
            }

    def get_documents(self, instance):
        documents = EcjuQueryDocument.objects.filter(query=instance)
        return SimpleEcjuQueryDocumentViewSerializer(documents, many=True).data


class EcjuQueryExporterRespondSerializer(serializers.ModelSerializer):
    team = serializers.SerializerMethodField()
    responded_by_user = PrimaryKeyRelatedSerializerField(
        queryset=ExporterUser.objects.all(), serializer=ExporterUserViewSerializer
    )
    response = serializers.CharField(max_length=2200, allow_blank=False, allow_null=False)
    documents = serializers.SerializerMethodField()

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
            "documents",
        )

    def get_team(self, instance):
        # If the team is not available, use the user's current team.
        team = instance.team if instance.team else instance.raised_by_user.team
        return TeamSerializer(team).data

    def get_documents(self, instance):
        documents = EcjuQueryDocument.objects.filter(query=instance)
        return SimpleEcjuQueryDocumentViewSerializer(documents, many=True).data


class EcjuQueryCreateSerializer(serializers.ModelSerializer):
    """
    Query CREATE serializer for GOV users
    Does not take a response as they cannot respond to their own queries
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
            "team",
        )


class EcjuQueryDocumentCreateSerializer(serializers.ModelSerializer):
    query = serializers.PrimaryKeyRelatedField(queryset=EcjuQuery.objects.all())
    user = serializers.PrimaryKeyRelatedField(queryset=ExporterUser.objects.all())

    class Meta:
        model = EcjuQueryDocument
        fields = (
            "name",
            "s3_key",
            "user",
            "size",
            "query",
            "description",
        )

    def create(self, validated_data):
        query_document = super().create(validated_data)
        query_document.save()
        process_document(query_document)
        return query_document


class EcjuQueryDocumentViewSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    created_at = serializers.DateTimeField()
    name = serializers.CharField()
    description = serializers.CharField()
    user = ExporterUserSimpleSerializer()
    s3_key = serializers.SerializerMethodField()
    safe = serializers.BooleanField()

    def get_s3_key(self, instance):
        return instance.s3_key if instance.safe else "File not ready"


class SimpleEcjuQueryDocumentViewSerializer(serializers.ModelSerializer):
    class Meta:
        model = EcjuQueryDocument
        fields = (
            "id",
            "name",
            "description",
            "size",
            "safe",
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


class ReviewDateUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for setting and editing the next review date of a case.
    """

    team = serializers.PrimaryKeyRelatedField(required=True, queryset=Team.objects.all())
    case = serializers.PrimaryKeyRelatedField(required=True, queryset=Case.objects.all())
    next_review_date = serializers.DateField(
        required=False,
        allow_null=True,
        error_messages={"invalid": strings.Cases.NextReviewDate.Errors.INVALID_DATE_FORMAT},
    )

    class Meta:
        model = CaseReviewDate
        fields = ("next_review_date", "team", "case")

    def validate_next_review_date(self, value):
        if value:
            today = timezone.now().date()
            if value < today:
                raise ValidationError(strings.Cases.NextReviewDate.Errors.DATE_IN_PAST)
        return value
