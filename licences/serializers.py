from rest_framework import serializers

from applications.enums import LicenceDuration
from applications.models import BaseApplication, GoodOnApplication, CountryOnApplication
from cases.enums import AdviceType
from cases.generated_documents.models import GeneratedCaseDocument
from conf.serializers import CountrySerializerField, KeyValueChoiceField
from goods.models import Good
from goodstype.models import GoodsType
from licences.models import Licence
from lite_content.lite_api import strings
from parties.models import Party
from static.statuses.serializers import CaseStatusSerializer


class LicenceCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Licence
        fields = (
            "application",
            "start_date",
            "duration",
            "is_complete",
        )

    def validate(self, data):
        """
        Check that the duration is valid
        """
        super().validate(data)
        if data.get("duration") and (
            data["duration"] > LicenceDuration.MAX.value or data["duration"] < LicenceDuration.MIN.value
        ):
            raise serializers.ValidationError(strings.Applications.Finalise.Error.DURATION_RANGE)
        return data


class CaseLicenceViewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Licence
        fields = (
            "start_date",
            "duration",
            "is_complete",
        )


class GoodLicenceListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Good
        fields = (
            "description",
            "control_code",
        )


class GoodsTypeOnLicenceListSerializer(serializers.ModelSerializer):
    class Meta:
        model = GoodsType
        fields = (
            "description",
            "control_code",
        )


class GoodOnLicenceListSerializer(serializers.ModelSerializer):
    good = GoodLicenceListSerializer(read_only=True)

    class Meta:
        model = GoodOnApplication
        fields = (
            "good",
            "quantity",
        )


class CountriesLicenceSerializer(serializers.ModelSerializer):
    country = CountrySerializerField()

    class Meta:
        model = CountryOnApplication
        fields = ("country",)


class PartyLicenceSerializer(serializers.ModelSerializer):
    country = CountrySerializerField()

    class Meta:
        model = Party
        fields = ("name", "country")


class DocumentLicenceListSerializer(serializers.ModelSerializer):
    advice_type = KeyValueChoiceField(choices=AdviceType.choices)

    class Meta:
        model = GeneratedCaseDocument
        fields = (
            "advice_type",
            "id",
        )


class ApplicationLicenceListSerializer(serializers.ModelSerializer):
    goods = serializers.SerializerMethodField()
    destinations = serializers.SerializerMethodField()
    status = CaseStatusSerializer()
    documents = serializers.SerializerMethodField()

    class Meta:
        model = BaseApplication
        fields = ("id", "reference_code", "destinations", "goods", "status", "documents")

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
        elif instance.openapplication.application_countries.exists():
            return CountriesLicenceSerializer(instance.openapplication.application_countries, many=True).data


class LicenceListSerializer(serializers.ModelSerializer):
    application = ApplicationLicenceListSerializer()

    class Meta:
        model = Licence
        fields = (
            "id",
            "application",
        )
        ordering = ["created_at"]
