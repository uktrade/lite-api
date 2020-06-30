from django.db.models import F
from rest_framework import serializers

from applications.models import BaseApplication, PartyOnApplication, GoodOnApplication
from cases.enums import CaseTypeSubTypeEnum, AdviceType, AdviceLevel
from cases.generated_documents.models import GeneratedCaseDocument
from cases.models import CaseType
from common.serializers import EnumField
from conf.serializers import KeyValueChoiceField, CountrySerializerField
from goods.models import Good
from goodstype.models import GoodsType
from licences.enums import LicenceStatus
from licences.helpers import get_approved_goods_types, get_approved_goods_on_application
from licences.models import Licence
from licences.serializers.view_licences import (
    PartyLicenceListSerializer,
    CountriesLicenceSerializer,
    GoodLicenceListSerializer,
)
from licences.service import get_goods_on_licence
from parties.enums import PartyRole
from parties.models import Party, PartyDocument
from static.control_list_entries.serializers import ControlListEntrySerializer
from static.statuses.serializers import CaseStatusSerializer
from static.units.enums import Units


# Case View


class CaseLicenceViewSerializer(serializers.ModelSerializer):
    status = EnumField(LicenceStatus, required=False)

    class Meta:
        model = Licence
        fields = (
            "start_date",
            "duration",
            "status",
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
    control_list_entries = ControlListEntrySerializer(many=True)

    class Meta:
        model = GoodsType
        fields = (
            "description",
            "control_list_entries",
            "usage",
        )
        read_only_fields = fields


class GoodOnLicenceSerializer(serializers.ModelSerializer):
    good = GoodLicenceListSerializer(read_only=True)
    unit = KeyValueChoiceField(choices=Units.choices)

    class Meta:
        model = GoodOnApplication
        fields = (
            "good",
            "quantity",
            "usage",
            "unit",
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
            return get_goods_on_licence(
                Licence.objects.filter(application=instance).last(), include_control_list_entries=True
            )
        elif instance.goods_type.exists():
            approved_goods_types = get_approved_goods_types(instance)
            return GoodsTypeOnLicenceSerializer(approved_goods_types, many=True).data
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


class NLRdocumentSerializer(serializers.ModelSerializer):
    case_reference = serializers.CharField(source="case.reference_code")
    goods = serializers.SerializerMethodField()
    destinations = serializers.SerializerMethodField()

    class Meta:
        model = GeneratedCaseDocument
        fields = (
            "id",
            "name",
            "case_id",
            "case_reference",
            "goods",
            "destinations",
            "advice_type",
        )

    def get_goods(self, instance):
        goods = Good.objects.prefetch_related("control_list_entries").filter(
            advice__case_id=instance.case_id,
            advice__type=AdviceType.NO_LICENCE_REQUIRED,
            advice__level=AdviceLevel.FINAL,
        )
        return GoodLicenceListSerializer(goods, many=True).data

    def get_destinations(self, instance):
        return (
            Party.objects.filter(parties_on_application__application_id=instance.case_id)
            .order_by("country__name")
            .annotate(party_name=F("name"), country_name=F("country__name"))
            .values("party_name", "country_name")
        )
