from rest_framework import serializers
from rest_framework.fields import empty

from api.applications.models import BaseApplication
from api.cases.enums import CaseTypeSubTypeEnum
from api.core.serializers import ControlListEntryField, GoodControlReviewSerializer
from api.flags.enums import SystemFlags
from api.goods.enums import GoodControlled
from api.goodstype.constants import DESCRIPTION_MAX_LENGTH
from api.goodstype.document.models import GoodsTypeDocument
from api.goodstype.models import GoodsType
from api.staticdata.control_list_entries.serializers import ControlListEntrySerializer
from api.staticdata.countries.serializers import CountrySerializer


class GoodsTypeSerializer(serializers.ModelSerializer):
    description = serializers.CharField(max_length=DESCRIPTION_MAX_LENGTH)
    is_good_incorporated = serializers.BooleanField(required=True)
    is_good_controlled = serializers.BooleanField(required=True)
    control_list_entries = ControlListEntryField(many=True, required=False, allow_empty=True)
    application = serializers.PrimaryKeyRelatedField(queryset=BaseApplication.objects.all())
    document = serializers.SerializerMethodField()

    class Meta:
        model = GoodsType
        fields = (
            "id",
            "description",
            "application",
            "document",
            "is_good_incorporated",
            "is_good_controlled",
            "control_list_entries",
        )

    def __init__(self, *args, **kwargs):
        """
        Initializes serializer for Goods Type
        """
        super(GoodsTypeSerializer, self).__init__(*args, **kwargs)

        # Only add is_good_incorporated if application is of type OPEN
        # and not if it's a HMRC
        application = self.get_initial().get("application")

        if application and application.case_type.sub_type == CaseTypeSubTypeEnum.HMRC:
            if hasattr(self, "initial_data"):
                self.fields["is_good_incorporated"].required = False
                self.fields["is_good_incorporated"].allow_null = True
                self.fields["is_good_controlled"].required = False
                self.fields["is_good_controlled"].allow_null = True
                self.fields["control_list_entries"].required = False
                self.fields["control_list_entries"].allow_null = True
                self.initial_data["is_good_controlled"] = False
                self.initial_data["is_good_incorporated"] = None
                self.initial_data["control_list_entries"] = []

    def get_document(self, instance):
        docs = GoodsTypeDocument.objects.filter(goods_type=instance).values()
        return docs[0] if docs else None

    def update(self, instance, validated_data):
        """
        Update Goods Type Serializer
        """
        instance.description = validated_data.get("description", instance.description)
        instance.is_good_controlled = validated_data.get("is_good_controlled", instance.is_good_controlled)
        instance.control_list_entry = validated_data.get("control_list_entries", instance.control_list_entry)
        instance.is_good_incorporated = validated_data.get("is_good_incorporated", instance.is_good_incorporated)
        instance.save()
        return instance


class GoodsTypeViewSerializer(serializers.Serializer):
    id = serializers.UUIDField(read_only=True)
    description = serializers.CharField(read_only=True)
    is_good_controlled = serializers.ChoiceField(choices=GoodControlled.choices)
    is_good_incorporated = serializers.BooleanField(read_only=True)
    control_list_entries = ControlListEntrySerializer(many=True, read_only=True)
    countries = serializers.SerializerMethodField()
    document = serializers.SerializerMethodField()
    flags = serializers.SerializerMethodField()
    comment = serializers.CharField()
    report_summary = serializers.CharField(allow_blank=True, required=False)
    end_use_control = serializers.ListField(child=serializers.CharField(), required=False)

    def __init__(self, instance=None, data=empty, default_countries=None, **kwargs):
        super().__init__(instance, data, **kwargs)
        self.default_countries = default_countries

    def get_flags(self, instance):
        return list(instance.flags.filter().values("id", "name", "colour", "label"))

    def get_countries(self, instance):
        countries = instance.countries
        if not countries.count():
            return CountrySerializer(self.default_countries or [], many=True).data
        return CountrySerializer(countries, many=True).data

    def get_document(self, instance):
        docs = GoodsTypeDocument.objects.filter(goods_type=instance).values()
        return docs[0] if docs else None


class ClcControlGoodTypeSerializer(GoodControlReviewSerializer):
    class Meta(GoodControlReviewSerializer.Meta):
        model = GoodsType
        fields = GoodControlReviewSerializer.Meta.fields + ("end_use_control",)

    def update(self, instance, validated_data):
        instance.flags.remove(SystemFlags.GOOD_NOT_YET_VERIFIED_ID)
        return super().update(instance, validated_data)
