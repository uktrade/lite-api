from rest_framework import serializers

from applications.models import GoodOnApplication, CountryOnApplication, BaseApplication
from cases.enums import AdviceType
from cases.generated_documents.models import GeneratedCaseDocument
from conf.serializers import CountrySerializerField, KeyValueChoiceField, ControlListEntryField
from goods.models import Good
from goodstype.models import GoodsType
from licences.enums import LicenceStatus
from licences.helpers import serialize_goods_on_licence
from licences.models import Licence
from parties.models import Party


class GoodLicenceListSerializer(serializers.ModelSerializer):
    control_list_entries = ControlListEntryField(many=True)

    class Meta:
        model = Good
        fields = (
            "description",
            "control_list_entries",
        )
        read_only_fields = fields


class GoodsTypeOnLicenceListSerializer(serializers.ModelSerializer):
    control_list_entries = ControlListEntryField(many=True)

    class Meta:
        model = GoodsType
        fields = (
            "id",
            "description",
            "control_list_entries",
            "usage",
        )
        read_only_fields = fields


class GoodOnLicenceListSerializer(serializers.ModelSerializer):
    good = GoodLicenceListSerializer(read_only=True)

    class Meta:
        model = GoodOnApplication
        fields = ("good",)
        read_only_fields = fields


class CountriesLicenceSerializer(serializers.ModelSerializer):
    country = CountrySerializerField()

    class Meta:
        model = CountryOnApplication
        fields = ("country",)
        read_only_fields = fields


class PartyLicenceListSerializer(serializers.ModelSerializer):
    country = CountrySerializerField()

    class Meta:
        model = Party
        fields = (
            "name",
            "address",
            "country",
        )
        read_only_fields = fields


class DocumentLicenceListSerializer(serializers.ModelSerializer):
    advice_type = KeyValueChoiceField(choices=AdviceType.choices)

    class Meta:
        model = GeneratedCaseDocument
        fields = (
            "advice_type",
            "id",
        )
        read_only_fields = fields


class ApplicationLicenceListSerializer(serializers.ModelSerializer):
    destinations = serializers.SerializerMethodField()
    documents = serializers.SerializerMethodField()

    class Meta:
        model = BaseApplication
        fields = (
            "id",
            "name",
            "destinations",
            "documents",
        )
        read_only_fields = fields

    def get_documents(self, instance):
        documents = (
            GeneratedCaseDocument.objects.filter(case=instance, advice_type__isnull=False, visible_to_exporter=True)
            .order_by("advice_type", "-updated_at")
            .distinct("advice_type")
        )
        return DocumentLicenceListSerializer(documents, many=True).data

    def get_destinations(self, instance):
        if instance.end_user:
            return [PartyLicenceListSerializer(instance.end_user.party).data]
        elif hasattr(instance, "openapplication") and instance.openapplication.application_countries.exists():
            return CountriesLicenceSerializer(instance.openapplication.application_countries, many=True).data


class LicenceListSerializer(serializers.ModelSerializer):
    application = ApplicationLicenceListSerializer()
    goods = serializers.SerializerMethodField()
    status = KeyValueChoiceField(choices=LicenceStatus.choices)

    class Meta:
        model = Licence
        fields = (
            "id",
            "reference_code",
            "status",
            "application",
            "goods",
        )
        read_only_fields = fields
        ordering = ["created_at"]

    def get_goods(self, instance):
        return serialize_goods_on_licence(instance)
