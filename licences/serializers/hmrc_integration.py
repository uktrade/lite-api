from rest_framework import serializers

from applications.models import GoodOnApplication
from conf.helpers import add_months
from goods.models import Good
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


class HMRCIntegrationGoodUsageUpdateSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    usage = serializers.IntegerField()


class HMRCIntegrationLicenceUpdateSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    goods = HMRCIntegrationGoodUsageUpdateSerializer(many=True)


class HMRCIntegrationLicencesUpdateSerializer(serializers.Serializer):
    licences = HMRCIntegrationLicenceUpdateSerializer(many=True)

    def validate(self, data):
        data = super(HMRCIntegrationLicencesUpdateSerializer, self).validate(data)
        data["licences"] = [self._validate_licence(licence) for licence in data["licences"]]
        return data

    def _validate_licence(self, data):
        try:
            data["id"] = Licence.objects.get(id=data["id"])
        except Licence.DoesNotExist:
            raise serializers.ValidationError({"licence": f"Licence '{data['id']}' not found."})

        data["goods"] = [self._validate_good(data["id"], good) for good in data["goods"]]

        return data

    def _validate_good(self, licence, data):
        try:
            data["id"] = GoodOnApplication.objects.get(application=licence.application, good_id=data["id"])
        except GoodOnApplication.DoesNotExist:
            raise serializers.ValidationError({"good": f"Good '{data['id']}' not found on Licence '{licence.id}'"})

        return data

    def create(self, validated_data):
        for licence in validated_data["licences"]:
            for good in licence["goods"]:
                goa = good["id"]
                goa.usage = good["usage"]
                goa.save()

        return validated_data
