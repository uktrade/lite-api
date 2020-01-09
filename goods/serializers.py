from rest_framework import serializers
from rest_framework.relations import PrimaryKeyRelatedField

from conf.helpers import str_to_bool
from conf.serializers import KeyValueChoiceField, ControlListEntryField
from documents.libraries.process_document import process_document
from goods.enums import GoodStatus, GoodControlled
from goods.libraries.get_goods import get_good_query_with_notifications
from goods.models import Good, GoodDocument
from gov_users.serializers import GovUserSimpleSerializer
from lite_content.lite_api import strings
from organisations.models import Organisation
from organisations.serializers import OrganisationDetailSerializer
from picklists.models import PicklistItem
from queries.control_list_classifications.models import ControlListClassificationQuery
from static.missing_document_reasons.enums import GoodMissingDocumentReasons
from static.statuses.libraries.get_case_status import get_status_value_from_case_status_enum
from users.libraries.get_user import get_user_by_pk
from users.models import ExporterUser
from users.serializers import ExporterUserSimpleSerializer


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
    is_good_controlled = serializers.ChoiceField(
        choices=GoodControlled.choices, error_messages={"required": strings.Goods.FORM_DEFAULT_ERROR_RADIO_REQUIRED},
    )
    control_code = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    is_good_end_product = serializers.BooleanField(
        error_messages={"required": strings.Goods.FORM_DEFAULT_ERROR_RADIO_REQUIRED}
    )
    organisation = PrimaryKeyRelatedField(queryset=Organisation.objects.all())
    status = KeyValueChoiceField(choices=GoodStatus.choices)
    not_sure_details_details = serializers.CharField(allow_blank=True, required=False)
    case_id = serializers.SerializerMethodField()
    case_officer = serializers.SerializerMethodField()
    query = serializers.SerializerMethodField()
    case_status = serializers.SerializerMethodField()
    documents = serializers.SerializerMethodField()
    missing_document_reason = KeyValueChoiceField(choices=GoodMissingDocumentReasons.choices, read_only=True)

    class Meta:
        model = Good
        fields = (
            "id",
            "description",
            "is_good_controlled",
            "case_id",
            "case_officer",
            "control_code",
            "is_good_end_product",
            "part_number",
            "organisation",
            "status",
            "not_sure_details_details",
            "query",
            "documents",
            "case_status",
            "missing_document_reason",
        )

    def __init__(self, *args, **kwargs):
        super(GoodSerializer, self).__init__(*args, **kwargs)

        if self.get_initial().get("is_good_controlled") == GoodControlled.YES:
            self.fields["control_code"] = ControlListEntryField(required=True)
        else:
            if hasattr(self, "initial_data"):
                self.initial_data["control_code"] = None

    # pylint: disable=W0703
    def get_case_id(self, instance):
        clc_query = ControlListClassificationQuery.objects.filter(good=instance)
        if clc_query:
            return clc_query.first().id

    def get_case_officer(self, instance):
        clc_query_qs = ControlListClassificationQuery.objects.filter(good=instance, case_officer__isnull=False)
        if clc_query_qs:
            user = get_user_by_pk(clc_query_qs.first().case_officer)
            return GovUserSimpleSerializer(user).data

    def get_query(self, instance):
        return get_good_query_with_notifications(
            good=instance, exporter_user=self.context.get("exporter_user"), total_count=False
        )

    def get_case_status(self, instance):
        try:
            clc_query = ControlListClassificationQuery.objects.get(good=instance)
            return {
                "key": clc_query.status.status,
                "value": get_status_value_from_case_status_enum(clc_query.status.status),
            }
        except ControlListClassificationQuery.DoesNotExist:
            return None

    def get_documents(self, instance):
        documents = GoodDocument.objects.filter(good=instance)
        if documents:
            return SimpleGoodDocumentViewSerializer(documents, many=True).data

    def validate(self, value):
        is_controlled_good = value.get("is_good_controlled") == GoodControlled.YES
        if is_controlled_good and not value.get("control_code"):
            raise serializers.ValidationError("Control Code must be set when good is controlled")

        return value

    def update(self, instance, validated_data):
        instance.description = validated_data.get("description", instance.description)
        instance.is_good_controlled = validated_data.get("is_good_controlled", instance.is_good_controlled)
        instance.control_code = validated_data.get("control_code", "")
        instance.is_good_end_product = validated_data.get("is_good_end_product", instance.is_good_end_product)
        instance.part_number = validated_data.get("part_number", instance.part_number)
        instance.status = validated_data.get("status", instance.status)
        instance.save()
        return instance


class GoodMissingDocumentSerializer(serializers.ModelSerializer):
    missing_document_reason = KeyValueChoiceField(
        choices=GoodMissingDocumentReasons.choices,
        allow_blank=True,
        required=False,
        error_messages={"invalid_choice": strings.Goods.INVALID_MISSING_DOCUMENT_REASON},
    )

    class Meta:
        model = Good
        fields = ("id", "missing_document_reason")


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
