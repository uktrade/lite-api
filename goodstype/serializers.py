from rest_framework import serializers

from applications.enums import ApplicationType
from applications.libraries.get_applications import get_application
from applications.models import BaseApplication
from conf.helpers import str_to_bool
from conf.serializers import ControlListEntryField
from flags.enums import FlagStatuses
from goodstype.constants import DESCRIPTION_MAX_LENGTH
from goodstype.document.models import GoodsTypeDocument
from goodstype.models import GoodsType
from lite_content.lite_api import strings
from picklists.models import PicklistItem
from static.countries.models import Country
from static.countries.serializers import CountrySerializer


class GoodsTypeSerializer(serializers.ModelSerializer):
    description = serializers.CharField(max_length=DESCRIPTION_MAX_LENGTH)
    control_code = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    is_good_controlled = serializers.BooleanField()
    application = serializers.PrimaryKeyRelatedField(queryset=BaseApplication.objects.all())
    countries = serializers.SerializerMethodField()
    document = serializers.SerializerMethodField()

    class Meta:
        model = GoodsType
        fields = (
            "id",
            "description",
            "is_good_controlled",
            "control_code",
            "application",
            "countries",
            "document",
        )

    def __init__(self, *args, **kwargs):
        """
        Initializes serializer for Goods Type
        """
        super(GoodsTypeSerializer, self).__init__(*args, **kwargs)

        # Only add is_good_incorporated if application is of type OPEN_LICENCE
        # and not if it's a HMRC_QUERY
        application = self.get_initial().get("application")
        if application:
            if get_application(application).application_type == ApplicationType.OPEN_LICENCE:
                self.fields["is_good_incorporated"] = serializers.BooleanField()
                self.Meta.fields = self.Meta.fields + ("is_good_incorporated",)
            else:
                if hasattr(self, "initial_data"):
                    self.initial_data["is_good_incorporated"] = None

        # Only validate the control code if the good is controlled
        if str_to_bool(self.get_initial().get("is_good_controlled")) is True:
            self.fields["control_code"] = ControlListEntryField(required=True)
        else:
            if hasattr(self, "initial_data"):
                self.initial_data["control_code"] = None

    def get_countries(self, instance):
        countries = instance.countries
        if not countries.count():
            countries = Country.objects.filter(countries_on_application__application=instance.application)
        return CountrySerializer(countries, many=True).data

    def get_document(self, instance):
        docs = GoodsTypeDocument.objects.filter(goods_type=instance).values()
        return docs[0] if docs else None

    def update(self, instance, validated_data):
        """
        Update Goods Type Serializer
        """
        instance.description = validated_data.get("description", instance.description)
        instance.is_good_controlled = validated_data.get("is_good_controlled", instance.is_good_controlled)
        instance.control_code = validated_data.get("control_code", instance.control_code)
        instance.is_good_incorporated = validated_data.get("is_good_incorporated", instance.is_good_incorporated)
        instance.save()
        return instance


class FullGoodsTypeSerializer(GoodsTypeSerializer):
    flags = serializers.SerializerMethodField()

    def get_flags(self, instance):
        return list(instance.flags.filter(status=FlagStatuses.ACTIVE).values("id", "name"))

    class Meta:
        model = GoodsType
        fields = "__all__"


class ClcControlGoodTypeSerializer(serializers.ModelSerializer):
    control_code = serializers.CharField(required=False, allow_blank=True, allow_null=True, write_only=True)
    is_good_controlled = serializers.BooleanField
    comment = serializers.CharField(allow_blank=True, max_length=500, required=True, allow_null=True)
    report_summary = serializers.PrimaryKeyRelatedField(
        queryset=PicklistItem.objects.all(), required=False, allow_null=True
    )

    class Meta:
        model = GoodsType
        fields = (
            "control_code",
            "is_good_controlled",
            "comment",
            "report_summary",
        )

    def __init__(self, *args, **kwargs):
        super(ClcControlGoodTypeSerializer, self).__init__(*args, **kwargs)

        # Only validate the control code if the good is controlled
        if self.get_initial().get("is_good_controlled") == "True":
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
        if instance.is_good_controlled:
            instance.control_code = validated_data.get("control_code")
        else:
            instance.control_code = ""
        instance.flags.clear()

        instance.save()

        return instance
