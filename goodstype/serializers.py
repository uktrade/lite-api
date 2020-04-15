from rest_framework import serializers
from rest_framework.relations import PrimaryKeyRelatedField

from applications.libraries.get_applications import get_application
from applications.models import BaseApplication
from common.libraries import (
    update_good_or_goods_type_control_code_details,
    initialize_good_or_goods_type_control_code_serializer,
)
from cases.enums import CaseTypeSubTypeEnum
from conf.helpers import str_to_bool
from conf.serializers import ControlListEntryField, PrimaryKeyRelatedSerializerField
from goodstype.constants import DESCRIPTION_MAX_LENGTH
from goodstype.document.models import GoodsTypeDocument
from goodstype.models import GoodsType
from picklists.models import PicklistItem
from static.control_list_entries.models import ControlListEntry
from static.countries.models import Country
from static.countries.serializers import CountrySerializer


class GoodsTypeSerializer(serializers.ModelSerializer):
    description = serializers.CharField(max_length=DESCRIPTION_MAX_LENGTH)
    application = serializers.PrimaryKeyRelatedField(queryset=BaseApplication.objects.all())
    countries = serializers.SerializerMethodField()
    document = serializers.SerializerMethodField()

    class Meta:
        model = GoodsType
        fields = (
            "id",
            "description",
            "application",
            "countries",
            "document",
        )

    def __init__(self, *args, **kwargs):
        """
        Initializes serializer for Goods Type
        """
        super(GoodsTypeSerializer, self).__init__(*args, **kwargs)

        # Only add is_good_incorporated if application is of type OPEN
        # and not if it's a HMRC
        application = self.get_initial().get("application")
        if application:
            if get_application(application).case_type.sub_type == CaseTypeSubTypeEnum.OPEN:
                self.fields["is_good_incorporated"] = serializers.BooleanField(required=True)
                self.fields["is_good_controlled"] = serializers.BooleanField(required=True)
                self.fields["control_list_entries"] = PrimaryKeyRelatedSerializerField(
                    queryset=ControlListEntry.objects.all(), many=True, serializer=ControlListEntryField, required=False, allow_null=True, allow_empty=True
                )
                self.Meta.fields = self.Meta.fields + ("is_good_incorporated", "is_good_controlled", "control_code")
            else:
                if hasattr(self, "initial_data"):
                    self.initial_data["is_good_controlled"] = False
                    self.initial_data["is_good_incorporated"] = None

        # Only validate the control list entries if the good is controlled
        if str_to_bool(self.get_initial().get("is_good_controlled")) is True:
            self.fields["control_list_entries"] = serializers.PrimaryKeyRelatedField(queryset=ControlListEntry.objects.all(),
                                                                                     many=True,
                                                                                     required=False,
                                                                                     allow_null=True,
                                                                                     allow_empty=True)
        else:
            if hasattr(self, "initial_data"):
                self.initial_data["control_list_entries"] = None

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
        instance.control_code = validated_data.get("control_list_entries", instance.control_code)
        instance.is_good_incorporated = validated_data.get("is_good_incorporated", instance.is_good_incorporated)
        instance.save()
        return instance


class GoodsTypeViewSerializer(serializers.Serializer):
    description = serializers.CharField()


class FullGoodsTypeSerializer(GoodsTypeSerializer):
    flags = serializers.SerializerMethodField()

    def get_flags(self, instance):
        return list(instance.flags.filter().values("id", "name"))

    class Meta:
        model = GoodsType
        fields = "__all__"


class ClcControlGoodTypeSerializer(serializers.ModelSerializer):
    control_code = PrimaryKeyRelatedField(many=True, queryset=ControlListEntry.objects.all())
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
        initialize_good_or_goods_type_control_code_serializer(self)

    def update(self, instance, validated_data):
        instance.is_good_controlled = str_to_bool(validated_data.get("is_good_controlled"))
        instance = update_good_or_goods_type_control_code_details(instance, validated_data)
        instance.save()
        return instance
