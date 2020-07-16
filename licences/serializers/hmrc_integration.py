from rest_framework import serializers

from conf.helpers import add_months
from licences.enums import LicenceStatus, HMRCIntegrationActionEnum, licence_status_to_hmrc_integration_action
from licences.helpers import get_approved_goods_types
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


class HMRCIntegrationGoodOnLicenceSerializer(serializers.Serializer):
    id = serializers.UUIDField(source="good.good.id")
    usage = serializers.FloatField()
    description = serializers.CharField(source="good.good.description")
    unit = serializers.CharField(source="good.unit")
    quantity = serializers.FloatField()
    value = serializers.FloatField()


class HMRCIntegrationGoodsTypeSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    description = serializers.CharField()
    usage = serializers.IntegerField()


class HMRCIntegrationLicenceSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    reference = serializers.CharField(source="reference_code")
    type = serializers.CharField(source="application.case_type.reference")
    action = serializers.SerializerMethodField()  # 'insert', 'cancel' or 'update'
    old_id = serializers.SerializerMethodField()  # only required if action='update'
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

        self.action = licence_status_to_hmrc_integration_action.get(self.instance.status)
        if self.action != licence_status_to_hmrc_integration_action.get(LicenceStatus.REINSTATED):
            self.fields.pop("old_id")

    def get_action(self, _):
        return self.action

    def get_old_id(self, instance):
        return str(
            Licence.objects.filter(application=instance.application, status=LicenceStatus.CANCELLED)
            .order_by("created_at")
            .values_list("id", flat=True)
            .last()
        )

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
        if instance.goods.exists():
            return HMRCIntegrationGoodOnLicenceSerializer(instance.goods, many=True).data
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
    action = serializers.CharField(required=True, allow_null=False)
    goods = serializers.ListField(required=True, allow_null=False, allow_empty=True)


class HMRCIntegrationUsageUpdateLicencesSerializer(serializers.Serializer):
    usage_update_id = serializers.UUIDField(required=True, allow_null=False)
    licences = serializers.ListField(required=True, allow_null=False, allow_empty=False)
