from rest_framework import serializers

from addresses.serializers import AddressSerializer
from applications.models import BaseApplication, PartyOnApplication, GoodOnApplication
from cases.enums import CaseTypeSubTypeEnum, AdviceType
from cases.generated_documents.models import GeneratedCaseDocument
from cases.models import CaseType
from conf.helpers import add_months
from conf.serializers import KeyValueChoiceField, CountrySerializerField
from goodstype.models import GoodsType
from licences.helpers import get_approved_goods_types, get_approved_goods_on_application
from licences.models import Licence
from licences.serializers.view_licences import (
    PartyLicenceListSerializer,
    CountriesLicenceSerializer,
    GoodLicenceListSerializer,
)
from organisations.models import Organisation
from parties.enums import PartyRole
from parties.models import Party, PartyDocument
from static.control_list_entries.serializers import ControlListEntrySerializer
from static.statuses.enums import CaseStatusEnum
from static.statuses.serializers import CaseStatusSerializer
from static.units.enums import Units


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


class OrganisationLicenceSerializer(serializers.ModelSerializer):
    address = serializers.SerializerMethodField()

    class Meta:
        model = Organisation
        fields = (
            "name",
            "address",
        )
        read_only_fields = fields

    def get_address(self, instance):
        return AddressSerializer(instance.primary_site.address).data


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
            approved_goods = get_approved_goods_on_application(instance)
            return GoodOnLicenceSerializer(approved_goods, many=True).data
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


class HMRCIntegrationLicenceSerializer(serializers.ModelSerializer):
    reference = serializers.SerializerMethodField()
    type = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    end_date = serializers.SerializerMethodField()
    organisation = serializers.SerializerMethodField()
    end_user = serializers.SerializerMethodField()
    countries = serializers.SerializerMethodField()
    goods = serializers.SerializerMethodField()

    class Meta:
        model = Licence
        fields = (
            "id",
            "reference",
            "type",
            "status",
            "start_date",
            "end_date",
            "organisation",
            "end_user",
            "countries",
            "goods",
        )
        read_only_fields = fields

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if not self.instance.application.end_user:
            self.fields.pop("end_user")

        if not (
            hasattr(self.instance.application, "openapplication")
            and self.instance.application.openapplication.application_countries.exists()
        ):
            self.fields.pop("countries")

    def get_reference(self, instance):
        return instance.application.reference_code

    def get_type(self, instance):
        return instance.application.case_type.reference

    def get_status(self, instance):
        return CaseStatusEnum.get_text(instance.application.status.status)

    def get_end_date(self, instance):
        return add_months(instance.start_date, instance.duration)

    def get_organisation(self, instance):
        return OrganisationLicenceSerializer(instance.application.organisation).data

    def get_end_user(self, instance):
        return PartyLicenceListSerializer(instance.application.end_user.party).data

    def get_countries(self, instance):
        return CountriesLicenceSerializer(instance.application.openapplication.application_countries, many=True).data

    def get_goods(self, instance):
        if instance.application.goods.exists():
            approved_goods = get_approved_goods_on_application(instance.application)
            return GoodOnLicenceSerializer(approved_goods, many=True).data

        if instance.application.goods_type.exists():
            approved_goods_types = get_approved_goods_types(instance.application)
            return GoodsTypeOnLicenceSerializer(approved_goods_types, many=True).data

        return []
