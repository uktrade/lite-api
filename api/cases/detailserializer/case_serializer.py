from rest_framework import serializers
from rest_framework.fields import ChoiceField
from api.queues.serializers import QueueListSerializer
from api.cases.models import CaseQueue, CaseReviewDate
from api.core.serializers import KeyValueChoiceField, PrimaryKeyRelatedSerializerField
from api.cases.enums import (
    CaseTypeTypeEnum,
    AdviceType,
    CaseDocumentState,
    CaseTypeSubTypeEnum,
    CaseTypeReferenceEnum,
    ECJUQueryType,
)
from api.goods.enums import PvGrading
from api.external_data.enums import DenialMatchCategory
from api.flags.enums import SystemFlags
from api.external_data.models import SanctionMatch
from api.applications.serializers.fields import CaseStatusField
from api.applications.mixins.serializers import PartiesSerializerMixin


class QueueSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    alias = serializers.CharField()
    joined_queue_at = serializers.DateField()


class CaseTypeSerializer(serializers.Serializer):
    reference = KeyValueChoiceField(choices=CaseTypeReferenceEnum.choices)
    type = KeyValueChoiceField(choices=CaseTypeTypeEnum.choices)
    sub_type = KeyValueChoiceField(choices=CaseTypeSubTypeEnum.choices)


class TeamSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    alias = serializers.CharField()


class UserSerializer(serializers.Serializer):
    id = serializers.SerializerMethodField()
    baseuser_ptr = serializers.SerializerMethodField()
    team = TeamSerializer()

    def get_baseuser_ptr(self, instance):
        return instance.baseuser_ptr.id

    def get_id(self, instance):
        return instance.baseuser_ptr.id


class CountersignAdviceSerializer(serializers.Serializer):
    countersigned_user = UserSerializer()
    valid = serializers.BooleanField()


class PvGradingSerializer(serializers.Serializer):
    prefix = serializers.CharField()
    suffix = serializers.CharField()
    grading = KeyValueChoiceField(choices=PvGrading.choices + PvGrading.choices_new)


class GoodsSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    is_good_controlled = serializers.BooleanField()
    pv_grading_details = serializers.SerializerMethodField()
    report_summary = serializers.CharField()

    def get_pv_drading_details(self, instance):
        return PvGradingSerializer(instance.pv_grading_details)


class AdviceSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    user = UserSerializer()
    type = serializers.CharField()
    text = serializers.CharField()
    note = serializers.CharField()
    is_refusal_note = serializers.BooleanField()
    level = serializers.CharField()
    type = KeyValueChoiceField(choices=AdviceType.choices)


class DenialMatchSerializer(serializers.Serializer):
    category = ChoiceField(choices=DenialMatchCategory.choices)
    entity_type = serializers.SerializerMethodField()


class SanctionMatchSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    name = serializers.CharField()
    list_name = serializers.CharField()
    elasticsearch_reference = serializers.CharField()
    is_revoked = serializers.BooleanField()
    MATCH_NAME_MAPPING = {
        SystemFlags.SANCTION_UN_SC_MATCH: "UN SC",
        SystemFlags.SANCTION_OFSI_MATCH: "OFSI",
        SystemFlags.SANCTION_UK_MATCH: "UK",
    }

    list_name = serializers.SerializerMethodField()

    def get_list_name(self, obj):
        return self.MATCH_NAME_MAPPING[obj.flag_uuid]


class AppealDocumentSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    name = serializers.CharField()
    size = serializers.CharField()
    s3_key = serializers.CharField()


class AppealSerializer(serializers.Serializer):
    documents = AppealDocumentSerializer(many=True, read_only=True)
    id = serializers.UUIDField()
    grounds_for_appeal = serializers.CharField()


class DataSerializer(PartiesSerializerMixin, serializers.Serializer):
    denial_matches = serializers.SerializerMethodField()
    sanction_matches = serializers.SerializerMethodField()
    appeal = AppealSerializer()
    status = CaseStatusField()
    case_type = CaseTypeSerializer()

    def get_denial_matches(self, instance):
        return DenialMatchSerializer(instance.denial_matches.filter(denial__is_revoked=False), many=True).data

    def get_sanction_matches(self, instance):
        queryset = SanctionMatch.objects.filter(party_on_application__application=instance, is_revoked=False)
        return SanctionMatchSerializer(queryset, many=True).data


class OrganisationSerializer(serializers.Serializer):
    id = serializers.UUIDField()


class CaseDetailSimpleSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    submitted_at = serializers.DateTimeField()
    case_type = CaseTypeSerializer()
    reference_code = serializers.CharField()
    queue_details = serializers.SerializerMethodField()
    advice = serializers.SerializerMethodField()
    countersign_advice = serializers.SerializerMethodField()
    data = serializers.SerializerMethodField()
    next_review_date = serializers.SerializerMethodField()
    organisation = OrganisationSerializer()
    case_officer = serializers.SerializerMethodField()
    assigned_users = serializers.SerializerMethodField()
    # goods = serializers.SerializerMethodField()

    def __init__(self, *args, **kwargs):
        self.team = kwargs.pop("team", None)
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

    def get_queue_details(self, instance):
        return QueueSerializer(instance.queues.all(), many=True).data

    def get_advice(self, instance):
        return AdviceSerializer(instance.advice.all(), many=True).data

    def get_countersign_advice(self, instance):
        return CountersignAdviceSerializer(instance.countersign_advice.all(), many=True).data

    def get_data(self, instance):
        return DataSerializer(instance.baseapplication).data

    def get_next_review_date(self, instance):
        try:
            return instance.case_review_date.get(case_id=instance.id, team_id=self.team.id).next_review_date
        except CaseReviewDate.DoesNotExist:
            pass

    def get_queue_details(self, instance):
        details = list(instance.queues.values("id", "name", "alias"))
        qs = CaseQueue.objects.filter(
            case_id=instance.id, queue_id__in=list(instance.queues.values_list("id", flat=True))
        )
        queue_map = {case_queue.queue_id: case_queue for case_queue in qs}
        for detail in details:
            case_queue = queue_map[detail["id"]]
            detail["joined_queue_at"] = case_queue.created_at
        return details

    def get_case_officer(self, instance):
        if instance.case_officer:
            return {
                "id": instance.case_officer.baseuser_ptr.id,
                "first_name": instance.case_officer.first_name,
                "last_name": instance.case_officer.last_name,
                "email": instance.case_officer.email,
            }

    def get_assigned_users(self, instance):
        return instance.get_assigned_users()

    # def get_goods(self, instance):
    #     return GoodsSerializer(instance.good, many=True)
