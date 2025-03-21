from __future__ import division

from django.db.models import F
from django.forms import ChoiceField
from rest_framework import serializers

from api.applications.models import BaseApplication, PartyOnApplication, GoodOnApplication
from api.cases.enums import CaseTypeSubTypeEnum, AdviceType, AdviceLevel
from api.cases.generated_documents.models import GeneratedCaseDocument
from api.cases.models import CaseType
from api.cases.serializers import SimpleAdviceSerializer
from api.core.serializers import KeyValueChoiceField, CountrySerializerField, ControlListEntryField
from api.goods.models import Good
from api.goods.enums import GoodControlled
from api.licences.enums import LicenceStatus
from api.licences.helpers import serialize_goods_on_licence
from api.licences.models import (
    GoodOnLicence,
    Licence,
)
from api.parties.enums import PartyRole
from api.parties.models import Party, PartyDocument
from api.staticdata.control_list_entries.serializers import ControlListEntrySerializer
from api.staticdata.units.enums import Units


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
        else:
            return None


class GoodOnLicenceViewSerializer(serializers.Serializer):
    good_on_application_id = serializers.UUIDField(source="good.id")
    usage = serializers.FloatField()
    name = serializers.CharField(source="good.good.name")
    description = serializers.CharField(source="good.good.description")
    units = KeyValueChoiceField(source="good.unit", choices=Units.choices)
    applied_for_quantity = serializers.FloatField(source="good.quantity")
    applied_for_value = serializers.FloatField(source="good.value")
    licenced_quantity = serializers.FloatField(source="quantity")
    licenced_value = serializers.FloatField(source="value")
    applied_for_value_per_item = serializers.SerializerMethodField()
    licenced_value_per_item = serializers.SerializerMethodField()
    is_good_controlled = KeyValueChoiceField(source="good.is_good_controlled", choices=GoodControlled.choices)
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


class GoodOnLicenceReportsViewSerializer(GoodOnLicenceViewSerializer):
    id = serializers.UUIDField()
    good_on_application_id = serializers.UUIDField(source="good.id")
    licence_id = serializers.UUIDField(source="licence.id")

    def get_advice(self, instance):
        # Reports do not require nested advice.
        return None


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


class LicenceDetailsSerializer(serializers.ModelSerializer):
    # These actions are used to support the Licence status change screen
    # Suspened to reinstated don't send HMRC messages as these are only support offline via email

    case_status = serializers.SerializerMethodField()
    status = ChoiceField(choices=LicenceStatus.choices)

    action_dict = {
        "reinstated": lambda instance, user: Licence.reinstate(instance, user),
        "suspended": lambda instance, user: Licence.suspend(instance, user),
        "revoked": lambda instance, user: Licence.revoke(instance, user),
    }

    class Meta:
        model = Licence
        fields = (
            "id",
            "reference_code",
            "status",
            "case_status",
        )
        read_only_fields = ["id", "reference_code", "case_status"]

    def update(self, instance, validated_data):
        update_action = validated_data.get("status")
        try:
            request = self.context.get("request")
            action_method = self.action_dict[update_action]
            action_method(instance, request.user)
        except KeyError:
            raise serializers.ValidationError(f"Updating licence status: {update_action} not allowed")

        return super().update(instance, validated_data)

    def get_case_status(self, instance):
        return instance.case.status.status


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


class GoodOnLicenceLicenceListSerializer(serializers.ModelSerializer):
    good_on_application_id = serializers.UUIDField(source="good.id")
    control_list_entries = ControlListEntrySerializer(source="good.good.control_list_entries", many=True)
    assessed_control_list_entries = ControlListEntrySerializer(source="good.control_list_entries", many=True)
    description = serializers.CharField(source="good.good.description")
    name = serializers.CharField(source="good.good.name")

    class Meta:
        model = GoodOnLicence
        fields = (
            "id",
            "good_on_application_id",
            "control_list_entries",
            "assessed_control_list_entries",
            "description",
            "name",
        )
        read_only_fields = fields


class LicenceListSerializer(serializers.ModelSerializer):
    application = ApplicationLicenceListSerializer(source="case.baseapplication")
    status = KeyValueChoiceField(choices=LicenceStatus.choices)
    goods = GoodOnLicenceLicenceListSerializer(many=True)

    class Meta:
        model = Licence
        fields = (
            "id",
            "application",
            "reference_code",
            "status",
            "goods",
        )
        read_only_fields = fields
        ordering = ["created_at"]


class GoodOnLicenceExporterLicenceViewSerializer(serializers.ModelSerializer):
    applied_for_quantity = serializers.FloatField(source="good.quantity")
    assessed_control_list_entries = ControlListEntrySerializer(source="good.control_list_entries", many=True)
    control_list_entries = ControlListEntrySerializer(source="good.good.control_list_entries", many=True)
    description = serializers.CharField(source="good.good.description")
    name = serializers.CharField(source="good.good.name")
    licenced_quantity = serializers.FloatField(source="quantity")
    licenced_value = serializers.FloatField(source="value")
    units = KeyValueChoiceField(source="good.unit", choices=Units.choices)
    usage = serializers.FloatField()

    class Meta:
        model = GoodOnLicence
        fields = (
            "id",
            "applied_for_quantity",
            "assessed_control_list_entries",
            "control_list_entries",
            "description",
            "licenced_quantity",
            "licenced_value",
            "name",
            "units",
            "usage",
        )
        read_only_fields = fields


class ExporterLicenceViewSerializer(serializers.ModelSerializer):
    application = ApplicationLicenceSerializer(source="case.baseapplication")
    document = serializers.SerializerMethodField()
    status = KeyValueChoiceField(choices=LicenceStatus.choices)
    goods = GoodOnLicenceExporterLicenceViewSerializer(many=True)

    class Meta:
        model = Licence
        fields = (
            "id",
            "application",
            "document",
            "duration",
            "goods",
            "reference_code",
            "start_date",
            "status",
        )
        read_only_fields = fields

    def get_document(self, instance):
        document = GeneratedCaseDocument.objects.get(licence=instance)
        return {"id": document.id}
