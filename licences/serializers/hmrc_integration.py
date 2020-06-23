from rest_framework import serializers

from applications.models import GoodOnApplication
from cases.enums import CaseTypeEnum
from conf.helpers import add_months
from licences.helpers import get_approved_goods_types, get_approved_goods_on_application
from licences.models import Licence
from static.countries.models import Country


class HMRCIntegrationCountrySerializer(serializers.Serializer):
    id = serializers.CharField()
    name = serializers.CharField()


class HMRCIntegrationAddressSerializer(serializers.Serializer):
    line_1 = serializers.SerializerMethodField()
    line_2 = serializers.CharField(source="address_line_1")
    line_3 = serializers.CharField(source="address_line_2")
    line_4 = serializers.CharField(source="city")
    line_5 = serializers.CharField(source="region")
    postcode = serializers.CharField()
    country = HMRCIntegrationCountrySerializer()

    def __init__(self, *args, **kwargs):
        self._address_name = kwargs.pop("address_name")
        super().__init__(*args, **kwargs)

    def get_line_1(self, _):
        return self._address_name


class HMRCIntegrationOrganisationSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    name = serializers.CharField()
    address = serializers.SerializerMethodField()

    def get_address(self, instance):
        return HMRCIntegrationAddressSerializer(
            instance.primary_site.address, address_name=instance.primary_site.name
        ).data


class HMRCIntegrationEndUserSerializer(serializers.Serializer):
    name = serializers.CharField()
    address = serializers.SerializerMethodField()

    def get_address(self, instance):
        return {"line_1": instance.address, "country": HMRCIntegrationCountrySerializer(instance.country).data}


class HMRCIntegrationGoodOnApplicationSerializer(serializers.Serializer):
    id = serializers.UUIDField(source="good.id")
    description = serializers.CharField(source="good.description")
    usage = serializers.IntegerField()
    unit = serializers.CharField()
    quantity = serializers.IntegerField()
    licenced_quantity = serializers.IntegerField()
    licenced_value = serializers.IntegerField()


class HMRCIntegrationGoodsTypeSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    description = serializers.CharField()
    usage = serializers.IntegerField()


class HMRCIntegrationLicenceSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    reference = serializers.CharField(source="reference_code")
    type = serializers.CharField(source="application.case_type.reference")
    action = serializers.SerializerMethodField()  # `insert/cancel` on later story
    start_date = serializers.DateField()
    end_date = serializers.SerializerMethodField()
    organisation = HMRCIntegrationOrganisationSerializer(source="application.organisation")
    end_user = HMRCIntegrationEndUserSerializer(source="application.end_user.party")
    countries = serializers.SerializerMethodField()
    goods = serializers.SerializerMethodField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if not self.instance.application.end_user:
            self.fields.pop("end_user")

        if not (
            hasattr(self.instance.application, "openapplication")
            and self.instance.application.openapplication.application_countries.exists()
        ):
            self.fields.pop("countries")

    def get_action(self, _):
        return "insert"

    def get_end_date(self, instance):
        return add_months(instance.start_date, instance.duration, "%Y-%m-%d")

    def get_countries(self, instance):
        return HMRCIntegrationCountrySerializer(
            Country.objects.filter(countries_on_application__application=instance.application.openapplication).order_by(
                "name"
            ),
            many=True,
        ).data

    def get_goods(self, instance):
        if instance.application.goods.exists():
            approved_goods = get_approved_goods_on_application(instance.application)
            return HMRCIntegrationGoodOnApplicationSerializer(approved_goods, many=True).data
        elif instance.application.goods_type.exists():
            approved_goods_types = get_approved_goods_types(instance.application)
            return HMRCIntegrationGoodsTypeSerializer(approved_goods_types, many=True).data
        else:
            return []


class HMRCIntegrationUsageUpdateGoodSerializer(serializers.Serializer):
    id = serializers.UUIDField(required=True, allow_null=False)
    usage = serializers.FloatField(required=True, allow_null=False, min_value=0)


class HMRCIntegrationUsageUpdateLicenceSerializer(serializers.Serializer):
    id = serializers.UUIDField(required=True, allow_null=False)
    goods = HMRCIntegrationUsageUpdateGoodSerializer(many=True, required=True, allow_null=False, allow_empty=False)


class HMRCIntegrationUsageUpdateLicencesSerializer(serializers.Serializer):
    licences = HMRCIntegrationUsageUpdateLicenceSerializer(
        many=True, required=True, allow_null=False, allow_empty=False
    )

    def create(self, validated_data):
        """Updates the usages for Goods on Licences"""

        for licence in validated_data["licences"]:
            for good in licence["goods"]:
                gol = good["good_on_licence"]
                gol.usage = good["usage"]
                gol.save()
        return validated_data

    def validate(self, data):
        data = super(HMRCIntegrationUsageUpdateLicencesSerializer, self).validate(data)
        data["licences"] = [self._validate_licence(licence) for licence in data["licences"]]
        return data

    def _validate_licence(self, data: dict) -> dict:
        """Validates that a Licence exists and that the Goods exist on that Licence"""

        try:
            licence = Licence.objects.get(id=data["id"])
        except Licence.DoesNotExist:
            raise serializers.ValidationError({"licences": f"Licence '{data['id']}' not found."})

        if licence.application.case_type_id in CaseTypeEnum.OPEN_LICENCE_IDS:
            raise serializers.ValidationError(
                {
                    "licences": f"Licence type '{licence.application.case_type.reference}' cannot be updated; "
                    f"Licence '{licence.id}'."
                }
            )

        data["goods"] = [self._validate_good_on_licence(licence, good) for good in data["goods"]]
        return data

    def _validate_good_on_licence(self, licence: Licence, data: dict) -> dict:
        """Validates that a Good exists on a Licence"""

        try:
            data["good_on_licence"] = GoodOnApplication.objects.get(application=licence.application, good_id=data["id"])
        except GoodOnApplication.DoesNotExist:
            raise serializers.ValidationError({"goods": f"Good '{data['id']}' not found on Licence '{licence.id}'"})
        return data
