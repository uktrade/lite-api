from __future__ import division

from django.db.models import F
from rest_framework import serializers

from api.applications.models import BaseApplication, PartyOnApplication, GoodOnApplication
from cases.enums import CaseTypeSubTypeEnum, AdviceType, AdviceLevel
from cases.generated_documents.models import GeneratedCaseDocument
from cases.models import CaseType
from cases.serializers import SimpleAdviceSerializer
from api.conf.serializers import KeyValueChoiceField, CountrySerializerField, ControlListEntryField
from api.goods.models import Good
from api.goodstype.models import GoodsType
from licences.enums import LicenceStatus
from licences.helpers import serialize_goods_on_licence, get_approved_countries
from licences.models import Licence
from parties.enums import PartyRole
from parties.models import Party, PartyDocument
from static.control_list_entries.serializers import ControlListEntrySerializer
from static.units.enums import Units


# Case View


class CaseLicenceViewSerializer(serializers.ModelSerializer):
    status = KeyValueChoiceField(LicenceStatus.choices, required=False)

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
    destinations = serializers.SerializerMethodField()
    end_user = PartyOnApplicationSerializer()
    ultimate_end_users = PartyOnApplicationSerializer(many=True)
    consignee = PartyOnApplicationSerializer()
    third_parties = PartyOnApplicationSerializer(many=True)
    documents = serializers.SerializerMethodField()
    case_type = CaseSubTypeSerializer()

    class Meta:
        model = BaseApplication
        fields = (
            "id",
            "case_type",
            "name",
            "destinations",
            "end_user",
            "ultimate_end_users",
            "consignee",
            "third_parties",
            "documents",
        )
        read_only_fields = fields

    def get_documents(self, instance):
        documents = GeneratedCaseDocument.objects.filter(
            case=instance, advice_type__isnull=False, visible_to_exporter=True
        ).order_by("advice_type", "-updated_at")
        return DocumentLicenceSerializer(documents, many=True).data

    def get_destinations(self, instance):
        if instance.end_user:
            return [PartyLicenceListSerializer(instance.end_user.party).data]
        elif hasattr(instance, "openapplication") and instance.openapplication.application_countries.exists():
            return [
                {"country": country}
                for country in CountriesLicenceSerializer(get_approved_countries(instance), many=True).data
            ]
        else:
            return None


class GoodOnLicenceViewSerializer(serializers.Serializer):
    good_on_application_id = serializers.UUIDField(source="good.id")
    usage = serializers.FloatField()
    description = serializers.CharField(source="good.good.description")
    units = KeyValueChoiceField(source="good.unit", choices=Units.choices)
    applied_for_quantity = serializers.FloatField(source="good.quantity")
    applied_for_value = serializers.FloatField(source="good.value")
    licenced_quantity = serializers.FloatField(source="quantity")
    licenced_value = serializers.FloatField(source="value")
    applied_for_value_per_item = serializers.SerializerMethodField()
    licenced_value_per_item = serializers.SerializerMethodField()
    control_list_entries = ControlListEntrySerializer(source="good.good.control_list_entries", many=True)
    advice = serializers.SerializerMethodField()

    def get_advice(self, instance):
        advice = instance.good.good.advice.get(level=AdviceLevel.FINAL, case_id=instance.licence.case_id)
        return SimpleAdviceSerializer(instance=advice).data

    def get_applied_for_value_per_item(self, instance):
        if instance.good.value and instance.good.quantity:
            return float(instance.good.value) / instance.good.quantity

    def get_licenced_value_per_item(self, instance):
        if instance.value and instance.quantity:
            return float(instance.value) / instance.quantity


class LicenceSerializer(serializers.ModelSerializer):
    application = ApplicationLicenceSerializer(source="case.baseapplication")
    goods = serializers.SerializerMethodField()
    status = KeyValueChoiceField(choices=LicenceStatus.choices)
    document = serializers.SerializerMethodField()

    class Meta:
        model = Licence
        fields = (
            "application",
            "reference_code",
            "status",
            "start_date",
            "duration",
            "goods",
            "document",
        )
        read_only_fields = fields

    def get_goods(self, instance):
        return serialize_goods_on_licence(instance)

    def get_document(self, instance):
        document = GeneratedCaseDocument.objects.get(licence=instance)
        return {"id": document.id}


class LicenceWithGoodsViewSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    start_date = serializers.DateField()
    duration = serializers.IntegerField()
    goods_on_licence = GoodOnLicenceViewSerializer(source="goods", many=True)


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


# Licence list serializers


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


class CountriesLicenceSerializer(serializers.Serializer):
    id = serializers.CharField()
    name = serializers.CharField()


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
            return [
                {"country": country}
                for country in CountriesLicenceSerializer(get_approved_countries(instance), many=True).data
            ]


class LicenceListSerializer(serializers.ModelSerializer):
    application = ApplicationLicenceListSerializer(source="case.baseapplication")
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
