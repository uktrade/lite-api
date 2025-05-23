from rest_framework import serializers

from api.licences.enums import LicenceStatus, licence_status_to_hmrc_integration_action, HMRCIntegrationActionEnum
from api.licences.models import Licence


class HMRCIntegrationCountrySerializer(serializers.Serializer):
    id = serializers.SerializerMethodField()
    name = serializers.CharField()

    def get_id(self, instance):
        if instance.trading_country_code:
            return instance.trading_country_code
        return self.strip_territory_code(instance.id)

    def strip_territory_code(self, country_code):
        """Does nothing for "GB" but transforms "AE-DU" to "AE"."""
        return country_code.split("-")[0]


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
    eori_number = serializers.CharField()

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
    id = serializers.UUIDField(source="good.id")
    usage = serializers.FloatField()
    name = serializers.CharField(source="good.good.name")
    description = serializers.CharField(source="good.good.description")
    unit = serializers.CharField(source="good.unit")
    quantity = serializers.FloatField()
    value = serializers.FloatField()


class HMRCIntegrationLicenceSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    reference = serializers.CharField(source="reference_code")
    type = serializers.CharField(source="case.case_type.reference")
    action = serializers.SerializerMethodField()  # 'insert', 'cancel' or 'update'
    old_id = serializers.SerializerMethodField()  # only required if action='update'
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    organisation = HMRCIntegrationOrganisationSerializer(source="case.organisation")
    end_user = HMRCIntegrationEndUserSerializer(source="case.baseapplication.end_user.party")
    countries = serializers.SerializerMethodField()
    goods = serializers.SerializerMethodField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if not (hasattr(self.instance.case, "baseapplication") and self.instance.case.baseapplication.end_user):
            self.fields.pop("end_user")

        # Currently open applications are not supported so this predicate
        # will always evaluate to True and countries will be removed
        if (
            hasattr(self.instance.case, "baseapplication")
            and not (
                hasattr(self.instance.case.baseapplication, "openapplication")
                and self.instance.case.baseapplication.openapplication.application_countries.exists()
            )
            and not hasattr(self.instance.case, "opengenerallicencecase")
        ):
            self.fields.pop("countries")

        self.action = licence_status_to_hmrc_integration_action.get(self.instance.status)
        if self.action != HMRCIntegrationActionEnum.UPDATE:
            self.fields.pop("old_id")

    def get_action(self, _):
        return self.action

    def get_old_id(self, instance):
        return str(
            Licence.objects.filter(case=instance.case, status=LicenceStatus.CANCELLED)
            .order_by("created_at")
            .values_list("id", flat=True)
            .last()
        )

    # TODO: This needs to be re-implemented for open licences
    def get_countries(self, instance):
        return []  #  pragma: no cover

    def get_goods(self, instance):
        if instance.goods.exists():
            """The order in which we send to HMRC matters and the line number is the common reference
            which is used to refer the products when usage data is reported.
            We also list the products in the same order in licence pdf which is used by exporters
            when declaring goods at the customs check"""
            return HMRCIntegrationGoodOnLicenceSerializer(instance.goods.order_by("created_at"), many=True).data
        else:
            return []


class HMRCIntegrationUsageDataGoodSerializer(serializers.Serializer):
    id = serializers.UUIDField(required=True, allow_null=False)
    usage = serializers.FloatField(required=True, allow_null=False, min_value=0)


class HMRCIntegrationUsageDataLicenceSerializer(serializers.Serializer):
    id = serializers.UUIDField(required=True, allow_null=False)
    action = serializers.CharField(required=True, allow_null=False)
    goods = serializers.ListField(required=True, allow_null=False, allow_empty=True)


class HMRCIntegrationUsageDataLicencesSerializer(serializers.Serializer):
    usage_data_id = serializers.UUIDField(required=True, allow_null=False)
    licences = serializers.ListField(required=True, allow_null=False, allow_empty=False)
