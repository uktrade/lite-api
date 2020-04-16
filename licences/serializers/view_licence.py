from rest_framework import serializers

from applications.models import BaseApplication, PartyOnApplication, GoodOnApplication
from cases.enums import CaseTypeSubTypeEnum, AdviceType
from cases.generated_documents.models import GeneratedCaseDocument
from cases.models import CaseType, FinalAdvice
from conf.serializers import KeyValueChoiceField, CountrySerializerField
from goodstype.models import GoodsType
from licences.models import Licence
from licences.serializers.view_licences import (
    PartyLicenceListSerializer,
    CountriesLicenceSerializer,
    GoodLicenceListSerializer,
)
from parties.enums import PartyRole
from parties.models import Party, PartyDocument
from static.statuses.serializers import CaseStatusSerializer


# Case View


class CaseLicenceViewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Licence
        fields = (
            "start_date",
            "duration",
            "is_complete",
        )


# Licence View


class DocumentLicenceSerializer(serializers.ModelSerializer):
    advice_type = KeyValueChoiceField(choices=AdviceType.choices)

    class Meta:
        model = GeneratedCaseDocument
        fields = (
            "advice_type",
            "name",
            "id",
        )
        read_only_fields = fields


class GoodsTypeOnLicenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = GoodsType
        fields = (
            "description",
            "control_code",
            "usage",
        )
        read_only_fields = fields


class GoodOnLicenceSerializer(serializers.ModelSerializer):
    good = GoodLicenceListSerializer(read_only=True)

    class Meta:
        model = GoodOnApplication
        fields = (
            "good",
            "quantity",
            "usage",
            "licenced_quantity",
            "licenced_value",
        )
        read_only_fields = fields


class CaseSubTypeSerializer(serializers.ModelSerializer):
    sub_type = KeyValueChoiceField(choices=CaseTypeSubTypeEnum.choices)

    class Meta:
        model = CaseType
        fields = ("sub_type",)


class PartyLicenceSerializer(serializers.ModelSerializer):
    name = serializers.CharField()
    address = serializers.CharField()
    country = CountrySerializerField()
    document = serializers.SerializerMethodField()
    role = KeyValueChoiceField(choices=PartyRole.choices)

    class Meta:
        model = Party
        fields = (
            "id",
            "name",
            "address",
            "country",
            "document",
            "role",
        )

    def get_document(self, instance):
        docs = PartyDocument.objects.filter(party=instance)
        return docs.values()[0] if docs.exists() else None


class PartyOnApplicationSerializer(serializers.ModelSerializer):
    party = PartyLicenceSerializer()

    class Meta:
        fields = ("party",)
        model = PartyOnApplication


class ApplicationLicenceSerializer(serializers.ModelSerializer):
    goods = serializers.SerializerMethodField()
    destinations = serializers.SerializerMethodField()
    end_user = PartyOnApplicationSerializer()
    ultimate_end_users = PartyOnApplicationSerializer(many=True)
    consignee = PartyOnApplicationSerializer()
    third_parties = PartyOnApplicationSerializer(many=True)
    status = CaseStatusSerializer()
    documents = serializers.SerializerMethodField()
    case_type = CaseSubTypeSerializer()

    class Meta:
        model = BaseApplication
        fields = (
            "id",
            "case_type",
            "name",
            "reference_code",
            "destinations",
            "goods",
            "end_user",
            "ultimate_end_users",
            "consignee",
            "third_parties",
            "status",
            "documents",
        )
        read_only_fields = fields

    def get_documents(self, instance):
        documents = GeneratedCaseDocument.objects.filter(
            case=instance, advice_type__isnull=False, visible_to_exporter=True
        )
        return DocumentLicenceSerializer(documents, many=True).data

    def get_goods(self, instance):
        if instance.goods.exists():
            approved_goods = FinalAdvice.objects.filter(
                case__id=instance.id, type__in=[AdviceType.APPROVE, AdviceType.PROVISO]
            ).values_list("good", flat=True)
            goods = instance.goods.filter(good_id__in=approved_goods)
            return GoodOnLicenceSerializer(goods, many=True).data
        elif instance.goods_type.exists():
            approved_goods = FinalAdvice.objects.filter(
                case__id=instance.id, type__in=[AdviceType.APPROVE, AdviceType.PROVISO]
            ).values_list("goods_type", flat=True)
            goods = instance.goods_type.filter(id__in=approved_goods)
            return GoodsTypeOnLicenceSerializer(goods, many=True).data
        else:
            return None

    def get_destinations(self, instance):
        if instance.end_user:
            return [PartyLicenceListSerializer(instance.end_user.party).data]
        elif hasattr(instance, "openapplication") and instance.openapplication.application_countries.exists():
            return CountriesLicenceSerializer(instance.openapplication.application_countries, many=True).data
        else:
            return None


class LicenceSerializer(serializers.ModelSerializer):
    application = ApplicationLicenceSerializer()

    class Meta:
        model = Licence
        fields = (
            "application",
            "start_date",
            "duration",
        )
        read_only_fields = fields
