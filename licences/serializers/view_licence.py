from rest_framework import serializers

from applications.models import BaseApplication
from cases.enums import CaseTypeSubTypeEnum
from cases.generated_documents.models import GeneratedCaseDocument
from cases.models import CaseType
from conf.serializers import KeyValueChoiceField
from licences.models import Licence
from licences.serializers.view_licences import (
    PartyLicenceSerializer,
    CountriesLicenceSerializer,
    GoodsTypeOnLicenceListSerializer,
    GoodOnLicenceListSerializer,
    DocumentLicenceListSerializer,
)
from static.statuses.serializers import CaseStatusSerializer


class CaseLicenceViewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Licence
        fields = (
            "start_date",
            "duration",
            "is_complete",
        )


class CaseSubTypeSerializer(serializers.ModelSerializer):
    sub_type = KeyValueChoiceField(choices=CaseTypeSubTypeEnum.choices)

    class Meta:
        model = CaseType
        fields = (
            "sub_type",
        )


class ApplicationLicenceSerializer(serializers.ModelSerializer):
    goods = serializers.SerializerMethodField()
    destinations = serializers.SerializerMethodField()
    status = CaseStatusSerializer()
    documents = serializers.SerializerMethodField()

    class Meta:
        model = BaseApplication
        fields = ("id", "case_type", "name", "reference_code", "destinations", "goods", "status", "documents")
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


class LicenceSerializer(serializers.ModelSerializer):
    application = ApplicationLicenceSerializer()

    class Meta:
        model = Licence
        fields = ("application",)
        read_only_fields = fields
