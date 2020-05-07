from rest_framework import serializers
from rest_framework.relations import PrimaryKeyRelatedField

from common.libraries import (
    initialize_good_or_goods_type_control_list_entries_serializer,
    update_good_or_goods_type_control_list_entries_details,
)
from conf.serializers import KeyValueChoiceField, ControlListEntryField
from documents.libraries.process_document import process_document
from goods.enums import GoodStatus, GoodControlled, GoodPvGraded, PvGrading
from goods.libraries.get_goods import get_good_query_with_notifications
from goods.models import Good, GoodDocument, PvGradingDetails
from gov_users.serializers import GovUserSimpleSerializer
from lite_content.lite_api import strings
from organisations.models import Organisation
from organisations.serializers import OrganisationDetailSerializer
from picklists.models import PicklistItem
from queries.goods_query.models import GoodsQuery
from queries.goods_query.serializers import ExporterReadGoodQuerySerializer
from static.control_list_entries.serializers import ControlListEntryViewSerializer, ControlListEntrySerializerSimple
from static.missing_document_reasons.enums import GoodMissingDocumentReasons
from static.statuses.libraries.get_case_status import get_status_value_from_case_status_enum
from users.models import ExporterUser
from users.serializers import ExporterUserSimpleSerializer


class PvGradingDetailsSerializer(serializers.ModelSerializer):
    grading = KeyValueChoiceField(choices=PvGrading.choices, allow_null=True, allow_blank=True)
    custom_grading = serializers.CharField(allow_blank=True, allow_null=True)
    prefix = serializers.CharField(allow_blank=True, allow_null=True)
    suffix = serializers.CharField(allow_blank=True, allow_null=True)
    issuing_authority = serializers.CharField(allow_blank=False, allow_null=False)
    reference = serializers.CharField(allow_blank=False, allow_null=False)
    date_of_issue = serializers.DateField(
        allow_null=False,
        error_messages={"invalid": "Enter the products date of issue and include a day, month, year."},
    )

    class Meta:
        model = PvGradingDetails
        fields = (
            "grading",
            "custom_grading",
            "prefix",
            "suffix",
            "issuing_authority",
            "reference",
            "date_of_issue",
        )

    def validate(self, data):
        validated_data = super(PvGradingDetailsSerializer, self).validate(data)

        if not validated_data.get("grading") and not validated_data.get("custom_grading"):
            raise serializers.ValidationError({"custom_grading": strings.Goods.NO_CUSTOM_GRADING_ERROR})

        if validated_data.get("grading") and validated_data.get("custom_grading"):
            raise serializers.ValidationError(
                {"custom_grading": strings.Goods.PROVIDE_ONLY_GRADING_OR_CUSTOM_GRADING_ERROR}
            )

        return validated_data


class GoodListSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    description = serializers.CharField()
    control_list_entries = ControlListEntryViewSerializer(many=True)
    part_number = serializers.CharField()
    status = KeyValueChoiceField(choices=GoodStatus.choices)


class GoodCreateSerializer(serializers.ModelSerializer):
    """
    This serializer contains a nested creatable and writable serializer: PvGradingDetailsSerializer.
    By default, nested serializers provide the ability to only retrieve data;
    To make them writable and updatable you must override the create and update methods in the parent serializer.

    This serializer sometimes can contain OrderedDict instance types due to it's 'validate_only' nature.
    Because of this, each 'get' override must check the instance type before creating queries
    """

    description = serializers.CharField(
        max_length=280, error_messages={"blank": strings.Goods.FORM_DEFAULT_ERROR_TEXT_BLANK}
    )
    is_good_controlled = KeyValueChoiceField(
        choices=GoodControlled.choices, error_messages={"required": strings.Goods.FORM_DEFAULT_ERROR_RADIO_REQUIRED}
    )
    control_list_entries = ControlListEntryField(required=False, many=True, allow_null=True, allow_empty=True)
    organisation = PrimaryKeyRelatedField(queryset=Organisation.objects.all())
    status = KeyValueChoiceField(read_only=True, choices=GoodStatus.choices)
    not_sure_details_details = serializers.CharField(allow_blank=True, required=False)
    missing_document_reason = KeyValueChoiceField(choices=GoodMissingDocumentReasons.choices, read_only=True)
    is_pv_graded = KeyValueChoiceField(
        choices=GoodPvGraded.choices, error_messages={"required": strings.Goods.FORM_DEFAULT_ERROR_RADIO_REQUIRED}
    )
    pv_grading_details = PvGradingDetailsSerializer(allow_null=True, required=False)

    class Meta:
        model = Good
        fields = (
            "id",
            "description",
            "is_good_controlled",
            "control_list_entries",
            "part_number",
            "organisation",
            "status",
            "not_sure_details_details",
            "is_pv_graded",
            "pv_grading_details",
            "missing_document_reason",
            "comment",
            "report_summary",
        )

    def __init__(self, *args, **kwargs):
        super(GoodCreateSerializer, self).__init__(*args, **kwargs)

        if self.get_initial().get("is_good_controlled") == GoodControlled.YES:
            self.fields["control_list_entries"] = ControlListEntryField(required=True, many=True)
        else:
            if hasattr(self, "initial_data"):
                self.initial_data["control_list_entries"] = []

        self.goods_query_case = (
            GoodsQuery.objects.filter(good=self.instance).first() if isinstance(self.instance, Good) else None
        )

    def validate(self, value):
        is_controlled_good = value.get("is_good_controlled") == GoodControlled.YES
        if is_controlled_good and not value.get("control_list_entries"):
            raise serializers.ValidationError(
                {"control_list_entries": [strings.Goods.CONTROL_LIST_ENTRY_IF_CONTROLLED_ERROR]}
            )

        return value

    def create(self, validated_data):
        if validated_data.get("pv_grading_details"):
            validated_data["pv_grading_details"] = GoodCreateSerializer._create_pv_grading_details(
                validated_data["pv_grading_details"]
            )

        return super(GoodCreateSerializer, self).create(validated_data)

    def update(self, instance, validated_data):
        instance.description = validated_data.get("description", instance.description)
        instance.is_good_controlled = validated_data.get("is_good_controlled", instance.is_good_controlled)
        instance.control_list_entries.set(
            validated_data.get("control_list_entries", instance.control_list_entries.all())
        )
        instance.part_number = validated_data.get("part_number", instance.part_number)
        instance.status = validated_data.get("status", instance.status)
        instance.is_pv_graded = validated_data.get("is_pv_graded", instance.is_pv_graded)
        if validated_data.get("is_pv_graded"):
            instance.pv_grading_details = GoodCreateSerializer._create_update_or_delete_pv_grading_details(
                is_pv_graded=instance.is_pv_graded == GoodPvGraded.YES,
                pv_grading_details=validated_data.get("pv_grading_details"),
                instance=instance.pv_grading_details,
            )

        instance.save()
        return instance

    @staticmethod
    def _create_update_or_delete_pv_grading_details(is_pv_graded=False, pv_grading_details=None, instance=None):
        """
        Creates/Updates/Deletes PV Grading Details depending on the parameters supplied
        :param is_pv_graded: If the good is not PV Graded, ensure there are no PV Grading Details
        :param pv_grading_details: The PV Grading Details to be created or updated
        :param instance: If supplied, it implies the instance of PV Grading Details to be updated or deleted
        :return:
        """
        if not is_pv_graded and instance:
            return GoodCreateSerializer._delete_pv_grading_details(instance)

        if pv_grading_details:
            if instance:
                return GoodCreateSerializer._update_pv_grading_details(pv_grading_details, instance)

            return GoodCreateSerializer._create_pv_grading_details(pv_grading_details)

        return None

    @staticmethod
    def _create_pv_grading_details(pv_grading_details):
        return PvGradingDetailsSerializer.create(PvGradingDetailsSerializer(), validated_data=pv_grading_details)

    @staticmethod
    def _update_pv_grading_details(pv_grading_details, instance):
        return PvGradingDetailsSerializer.update(
            PvGradingDetailsSerializer(), validated_data=pv_grading_details, instance=instance,
        )

    @staticmethod
    def _delete_pv_grading_details(instance):
        instance.delete()
        return None


class GoodMissingDocumentSerializer(serializers.ModelSerializer):
    missing_document_reason = KeyValueChoiceField(
        choices=GoodMissingDocumentReasons.choices,
        allow_blank=False,
        required=True,
        error_messages={"invalid_choice": strings.Goods.INVALID_MISSING_DOCUMENT_REASON},
    )

    class Meta:
        model = Good
        fields = (
            "id",
            "missing_document_reason",
        )


class GoodDocumentCreateSerializer(serializers.ModelSerializer):
    good = serializers.PrimaryKeyRelatedField(queryset=Good.objects.all())
    user = serializers.PrimaryKeyRelatedField(queryset=ExporterUser.objects.all())
    organisation = serializers.PrimaryKeyRelatedField(queryset=Organisation.objects.all())

    class Meta:
        model = GoodDocument
        fields = (
            "name",
            "s3_key",
            "user",
            "organisation",
            "size",
            "good",
            "description",
        )

    def create(self, validated_data):
        good_document = super(GoodDocumentCreateSerializer, self).create(validated_data)
        good_document.save()
        process_document(good_document)
        return good_document


class GoodDocumentViewSerializer(serializers.ModelSerializer):
    created_at = serializers.DateTimeField(read_only=True)
    good = serializers.PrimaryKeyRelatedField(queryset=Good.objects.all())
    user = ExporterUserSimpleSerializer()
    organisation = OrganisationDetailSerializer()
    s3_key = serializers.SerializerMethodField()

    def get_s3_key(self, instance):
        return instance.s3_key if instance.safe else "File not ready"

    class Meta:
        model = GoodDocument
        fields = (
            "id",
            "name",
            "s3_key",
            "user",
            "organisation",
            "size",
            "good",
            "created_at",
            "safe",
            "description",
        )


class SimpleGoodDocumentViewSerializer(serializers.ModelSerializer):
    class Meta:
        model = GoodDocument
        fields = (
            "id",
            "name",
            "description",
            "size",
            "safe",
        )


class GoodsFlagSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    name = serializers.CharField()


class GoodSerializerInternal(serializers.Serializer):
    id = serializers.UUIDField()
    control_list_entries = ControlListEntrySerializerSimple(many=True)
    comment = serializers.CharField()
    is_good_controlled = serializers.CharField()
    report_summary = serializers.CharField()
    flags = GoodsFlagSerializer(many=True)


class GoodSerializerExporter(serializers.Serializer):
    id = serializers.UUIDField()
    description = serializers.CharField()
    control_list_entries = ControlListEntryField(many=True)
    part_number = serializers.CharField()
    is_good_controlled = KeyValueChoiceField(choices=GoodControlled.choices)
    is_pv_graded = KeyValueChoiceField(choices=GoodPvGraded.choices)


class GoodSerializerExporterFullDetail(GoodSerializerExporter):
    case_id = serializers.SerializerMethodField()
    documents = serializers.SerializerMethodField()
    missing_document_reason = KeyValueChoiceField(choices=GoodMissingDocumentReasons.choices)
    status = KeyValueChoiceField(choices=GoodStatus.choices)
    query = serializers.SerializerMethodField()
    case_officer = serializers.SerializerMethodField()

    def __init__(self, *args, **kwargs):
        super(GoodSerializerExporterFullDetail, self).__init__(*args, **kwargs)
        self.goods_query = GoodsQuery.objects.filter(good=self.instance).first()

    def get_case_id(self, instance):
        return str(self.goods_query.id) if self.goods_query else None

    def get_documents(self, instance):
        documents = GoodDocument.objects.filter(good=instance)
        if documents.exists():
            return SimpleGoodDocumentViewSerializer(documents, many=True).data
        return None

    def get_query(self, instance):
        if self.goods_query:
            serializer = ExporterReadGoodQuerySerializer(
                instance=self.goods_query, context={"exporter_user": self.context.get("exporter_user"), "total_count": False}
            )
            return serializer.data
        return None

    def get_case_officer(self, instance):
        if self.goods_query:
            return GovUserSimpleSerializer(self.goods_query.case_officer).data
        return None


class ClcControlGoodSerializer(serializers.ModelSerializer):
    is_good_controlled = serializers.ChoiceField(
        choices=GoodControlled.choices,
        allow_null=False,
        required=True,
        write_only=True,
        error_messages={"null": "This field is required."},
    )
    control_list_entries = ControlListEntryField(required=False, allow_null=True, write_only=True, many=True)
    comment = serializers.CharField(allow_blank=True, max_length=500, required=True, allow_null=True)
    report_summary = serializers.PrimaryKeyRelatedField(
        queryset=PicklistItem.objects.all(), required=False, allow_null=True
    )

    class Meta:
        model = Good
        fields = (
            "is_good_controlled",
            "control_list_entries",
            "comment",
            "report_summary",
        )

    def __init__(self, *args, **kwargs):
        super(ClcControlGoodSerializer, self).__init__(*args, **kwargs)
        initialize_good_or_goods_type_control_list_entries_serializer(self)

    def update(self, instance, validated_data):
        instance.is_good_controlled = validated_data.get("is_good_controlled")
        instance = update_good_or_goods_type_control_list_entries_details(instance, validated_data)
        instance.status = GoodStatus.VERIFIED
        instance.save()
        return instance
