from rest_framework import serializers

from applications.models import BaseApplication
from conf.helpers import str_to_bool
from conf.serializers import ControlListEntryField
from conf.serializers import PrimaryKeyRelatedSerializerField
from flags.enums import FlagStatuses
from goodstype.constants import DESCRIPTION_MAX_LENGTH
from goodstype.document.models import GoodsTypeDocument
from goodstype.models import GoodsType
from static.countries.models import Country
from static.countries.serializers import CountrySerializer


class GoodsTypeSerializer(serializers.ModelSerializer):
    description = serializers.CharField(max_length=DESCRIPTION_MAX_LENGTH)
    control_code = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    is_good_controlled = serializers.BooleanField()
    is_good_end_product = serializers.BooleanField()
    application = serializers.PrimaryKeyRelatedField(queryset=BaseApplication.objects.all())
    countries = PrimaryKeyRelatedSerializerField(
        required=False, queryset=Country.objects.all(), serializer=CountrySerializer, many=True
    )
    document = serializers.SerializerMethodField()

    class Meta:
        model = GoodsType
        fields = (
            "id",
            "description",
            "is_good_controlled",
            "control_code",
            "is_good_end_product",
            "application",
            "countries",
            "document",
        )

    def __init__(self, *args, **kwargs):
        """
        Initializes serializer for Goods Type
        """
        super(GoodsTypeSerializer, self).__init__(*args, **kwargs)

        # Only validate the control code if the good is controlled
        if str_to_bool(self.get_initial().get("is_good_controlled")) is True:
            self.fields["control_code"] = ControlListEntryField(required=True)
        else:
            if hasattr(self, "initial_data"):
                self.initial_data["control_code"] = None

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
        instance.is_good_end_product = validated_data.get("is_good_end_product", instance.is_good_end_product)
        instance.save()
        return instance


class FullGoodsTypeSerializer(GoodsTypeSerializer):
    flags = serializers.SerializerMethodField()

    def get_flags(self, instance):
        return list(instance.flags.filter(status=FlagStatuses.ACTIVE).values("id", "name"))

    class Meta:
        model = GoodsType
        fields = "__all__"
