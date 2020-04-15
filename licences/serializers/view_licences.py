from rest_framework import serializers

from applications.models import GoodOnApplication, CountryOnApplication, BaseApplication
from cases.enums import AdviceType
from cases.generated_documents.models import GeneratedCaseDocument
from conf.serializers import CountrySerializerField, KeyValueChoiceField
from goods.models import Good
from goodstype.models import GoodsType
from licences.models import Licence
from parties.models import Party
from static.statuses.serializers import CaseStatusSerializer


class GoodLicenceListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Good
        fields = (
            "description",
            "control_code",
        )
        read_only_fields = fields


class GoodsTypeOnLicenceListSerializer(serializers.ModelSerializer):
    class Meta:
        model = GoodsType
        fields = (
            "description",
            "control_code",
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


class PartyLicenceSerializer(serializers.ModelSerializer):
    country = CountrySerializerField()

    class Meta:
        model = Party
        fields = ("name", "country")
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
    goods = serializers.SerializerMethodField()
    destinations = serializers.SerializerMethodField()
    status = CaseStatusSerializer()
    documents = serializers.SerializerMethodField()

    class Meta:
        model = BaseApplication
        fields = ("id", "name", "reference_code", "destinations", "goods", "status", "documents")
        read_only_fields = fields

    def get_documents(self, instance):
        documents = GeneratedCaseDocument.objects.filter(
            case=instance, advice_type__isnull=False, visible_to_exporter=True
        )
        return DocumentLicenceListSerializer(documents, many=True).data

    def get_goods(self, instance):
        if instance.goods.exists():
            return GoodOnLicenceListSerializer(instance.goods, many=True).data
        elif instance.goods_type.exists():
            return GoodsTypeOnLicenceListSerializer(instance.goods_type, many=True).data
        else:
            return None

    def get_destinations(self, instance):
        if instance.end_user:
            return [PartyLicenceSerializer(instance.end_user.party).data]
        elif hasattr(instance, "openapplication") and instance.openapplication.application_countries.exists():
            return CountriesLicenceSerializer(instance.openapplication.application_countries, many=True).data
        else:
            return None


class LicenceListSerializer(serializers.ModelSerializer):
    application = ApplicationLicenceListSerializer()

    class Meta:
        model = Licence
        fields = (
            "id",
            "application",
        )
        read_only_fields = fields
        ordering = ["created_at"]
