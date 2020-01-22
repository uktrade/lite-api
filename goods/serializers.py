from rest_framework import serializers
from rest_framework.relations import PrimaryKeyRelatedField

from conf.helpers import str_to_bool
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
    date_of_issue = serializers.DateField(required=True)

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


class GoodListSerializer(serializers.ModelSerializer):
    description = serializers.CharField(max_length=280)
    control_code = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    status = KeyValueChoiceField(choices=GoodStatus.choices)
    documents = serializers.SerializerMethodField()
    is_good_controlled = serializers.ChoiceField(choices=GoodControlled.choices)
    query = serializers.SerializerMethodField()

    class Meta:
        model = Good
        fields = (
            "id",
            "description",
            "control_code",
            "is_good_controlled",
            "part_number",
            "status",
            "documents",
            "query",
            "missing_document_reason",
        )

    def get_documents(self, instance):
        documents = GoodDocument.objects.filter(good=instance)
        if documents:
            return SimpleGoodDocumentViewSerializer(documents, many=True).data

    def get_query(self, instance):
        return get_good_query_with_notifications(
            good=instance, exporter_user=self.context.get("exporter_user"), total_count=True
        )


class GoodSerializer(serializers.ModelSerializer):
    description = serializers.CharField(
        max_length=280, error_messages={"blank": strings.Goods.FORM_DEFAULT_ERROR_TEXT_BLANK}
    )
    is_good_controlled = KeyValueChoiceField(
        choices=GoodControlled.choices, error_messages={"required": strings.Goods.FORM_DEFAULT_ERROR_RADIO_REQUIRED}
    )
    control_code = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    organisation = PrimaryKeyRelatedField(queryset=Organisation.objects.all())
    status = KeyValueChoiceField(read_only=True, choices=GoodStatus.choices)
    not_sure_details_details = serializers.CharField(allow_blank=True, required=False)
    case_id = serializers.SerializerMethodField()
    case_officer = serializers.SerializerMethodField()
    query = serializers.SerializerMethodField()
    case_status = serializers.SerializerMethodField()
    documents = serializers.SerializerMethodField()
    missing_document_reason = KeyValueChoiceField(choices=GoodMissingDocumentReasons.choices, read_only=True)
    is_pv_graded = KeyValueChoiceField(
        choices=GoodPvGraded.choices, error_messages={"required": strings.Goods.FORM_DEFAULT_ERROR_RADIO_REQUIRED}
    )

    # This is a nested creatable and writable serializer.
    # By default, nested serializers provide the ability to only retrieve data;
    # To make them writable and updatable you must override the create and update methods in the parent serializer
    pv_grading_details = PvGradingDetailsSerializer(allow_null=True, required=False)

    class Meta:
        model = Good
        fields = (
            "id",
            "description",
            "is_good_controlled",
            "case_id",
            "case_officer",
            "control_code",
            "part_number",
            "organisation",
            "status",
            "not_sure_details_details",
            "query",
            "documents",
            "case_status",
            "is_pv_graded",
            "pv_grading_details",
            "missing_document_reason",
        )

    def __init__(self, *args, **kwargs):
        super(GoodSerializer, self).__init__(*args, **kwargs)

        if self.get_initial().get("is_good_controlled") == GoodControlled.YES:
            self.fields["control_code"] = ControlListEntryField(required=True)
        else:
            if hasattr(self, "initial_data"):
                self.initial_data["control_code"] = None

        # This removes data being passed forward from product grading forms on editing goods when not needed
        if not self.get_initial().get("is_pv_graded") == GoodPvGraded.YES:
            if hasattr(self, "initial_data"):
                self.initial_data["pv_grading_details"] = None

        self.goods_query_case = (
            GoodsQuery.objects.filter(good=self.instance).first() if isinstance(self.instance, Good) else None
        )

    def get_case_id(self, instance):
        return str(self.goods_query_case.id) if self.goods_query_case else None

    def get_case_officer(self, instance):
        if self.goods_query_case:
            return GovUserSimpleSerializer(self.goods_query_case.case_officer).data
        return None

    def get_query(self, instance):
        if isinstance(instance, Good):
            return get_good_query_with_notifications(
                good=instance, exporter_user=self.context.get("exporter_user"), total_count=False
            )

        return None

    def get_case_status(self, instance):
        if self.goods_query_case:
            return {
                "key": self.goods_query_case.status.status,
                "value": get_status_value_from_case_status_enum(self.goods_query_case.status.status),
            }

        return None

    def get_documents(self, instance):
        if isinstance(instance, Good):
            documents = GoodDocument.objects.filter(good=instance)
            if documents.exists():
                return SimpleGoodDocumentViewSerializer(documents, many=True).data

        return None

    def validate(self, value):
        is_controlled_good = value.get("is_good_controlled") == GoodControlled.YES
        if is_controlled_good and not value.get("control_code"):
            raise serializers.ValidationError("Control Code must be set when good is controlled")

        return value

    def create(self, validated_data):
        pv_grading_details = validated_data.pop("pv_grading_details", None)
        if pv_grading_details:
            pv_grading_details = GoodSerializer._create_pv_grading_details(pv_grading_details)

        return Good.objects.create(pv_grading_details=pv_grading_details, **validated_data)

    def update(self, instance, validated_data):
        instance.description = validated_data.get("description", instance.description)
        instance.is_good_controlled = validated_data.get("is_good_controlled", instance.is_good_controlled)
        instance.control_code = validated_data.get("control_code", "")
        instance.part_number = validated_data.get("part_number", instance.part_number)
        instance.status = validated_data.get("status", instance.status)
        instance.is_pv_graded = validated_data.get("is_pv_graded", instance.is_pv_graded)
        instance.pv_grading_details = GoodSerializer._create_update_or_delete_pv_grading_details(
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
            return GoodSerializer._delete_pv_grading_details(instance)

        if pv_grading_details:
            if instance:
                return GoodSerializer._update_pv_grading_details(pv_grading_details, instance)

            return GoodSerializer._create_pv_grading_details(pv_grading_details)

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
        allow_blank=True,
        required=False,
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


class GoodWithFlagsSerializer(GoodSerializer):
    flags = serializers.SerializerMethodField()

    def get_flags(self, instance):
        return list(instance.flags.values("id", "name"))

    class Meta:
        model = Good
        fields = "__all__"


class ClcControlGoodSerializer(serializers.ModelSerializer):
    control_code = serializers.CharField(required=False, allow_blank=True, allow_null=True, write_only=True)
    is_good_controlled = serializers.ChoiceField(
        choices=GoodControlled.choices,
        allow_null=False,
        required=True,
        write_only=True,
        error_messages={"null": "This field is required."},
    )
    comment = serializers.CharField(allow_blank=True, max_length=500, required=True, allow_null=True)
    report_summary = serializers.PrimaryKeyRelatedField(
        queryset=PicklistItem.objects.all(), required=False, allow_null=True
    )

    class Meta:
        model = Good
        fields = (
            "control_code",
            "is_good_controlled",
            "comment",
            "report_summary",
        )

    def __init__(self, *args, **kwargs):
        super(ClcControlGoodSerializer, self).__init__(*args, **kwargs)

        # Only validate the control code if the good is controlled
        if str_to_bool(self.get_initial().get("is_good_controlled")):
            self.fields["control_code"] = ControlListEntryField(required=True, write_only=True)
            self.fields["report_summary"] = serializers.PrimaryKeyRelatedField(
                queryset=PicklistItem.objects.all(),
                required=True,
                error_messages={
                    "required": strings.Picklists.REQUIRED_REPORT_SUMMARY,
                    "null": strings.Picklists.REQUIRED_REPORT_SUMMARY,
                },
            )

    # pylint: disable = W0221
    def update(self, instance, validated_data):
        # Update the good's details
        instance.comment = validated_data.get("comment")
        if validated_data["report_summary"]:
            instance.report_summary = validated_data.get("report_summary").text
        else:
            instance.report_summary = ""
        instance.is_good_controlled = validated_data.get("is_good_controlled")
        if instance.is_good_controlled == "yes":
            instance.control_code = validated_data.get("control_code")
        else:
            instance.control_code = ""
        instance.status = GoodStatus.VERIFIED
        instance.flags.clear()

        instance.save()

        return instance
