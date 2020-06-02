from rest_framework import serializers

from addresses.models import Address
from applications.models import GoodOnApplication
from conf.helpers import add_months
from goodstype.models import GoodsType
from licences.helpers import get_approved_goods_types, get_approved_goods_on_application
from licences.models import Licence
from organisations.models import Organisation
from parties.models import Party
from static.countries.models import Country
from static.statuses.enums import CaseStatusEnum


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
        return add_months(instance.start_date, instance.duration, "%Y-%m-%d")

    def get_organisation(self, instance):
        return HMRCIntegrationOrganisationSerializer(instance.application.organisation).data

    def get_end_user(self, instance):
        return HMRCIntegrationEndUserSerializer(instance.application.end_user.party).data

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
            return HMRCIntegrationGoodsOnApplicationSerializer(approved_goods, many=True).data

        if instance.application.goods_type.exists():
            approved_goods_types = get_approved_goods_types(instance.application)
            return HMRCIntegrationGoodsTypeSerializer(approved_goods_types, many=True).data

        return []


class HMRCIntegrationOrganisationSerializer(serializers.ModelSerializer):
    address = serializers.SerializerMethodField()

    class Meta:
        model = Organisation
        fields = (
            "name",
            "address",
        )
        read_only_fields = fields

    def get_address(self, instance):
        return HMRCIntegrationAddressSerializer(
            instance.primary_site.address, address_name=instance.primary_site.name
        ).data


class HMRCIntegrationAddressSerializer(serializers.ModelSerializer):
    line_1 = serializers.SerializerMethodField()
    line_2 = serializers.SerializerMethodField()
    line_3 = serializers.SerializerMethodField()
    line_4 = serializers.SerializerMethodField()
    line_5 = serializers.SerializerMethodField()
    country = serializers.SerializerMethodField()

    class Meta:
        model = Address
        fields = (
            "line_1",
            "line_2",
            "line_3",
            "line_4",
            "line_5",
            "postcode",
            "country",
        )
        read_only_fields = fields

    def __init__(self, *args, **kwargs):
        self._address_name = kwargs.pop("address_name")
        super().__init__(*args, **kwargs)

    def get_line_1(self, _):
        return self._address_name

    def get_line_2(self, instance):
        return instance.address_line_1

    def get_line_3(self, instance):
        return instance.address_line_2

    def get_line_4(self, instance):
        return instance.city

    def get_line_5(self, instance):
        return instance.region

    def get_country(self, instance):
        return HMRCIntegrationCountrySerializer(instance.country).data


class HMRCIntegrationEndUserSerializer(serializers.ModelSerializer):
    address = serializers.SerializerMethodField()

    class Meta:
        model = Party
        fields = (
            "name",
            "address",
        )
        read_only_fields = fields

    def get_address(self, instance):
        return {"line_1": instance.address, "country": HMRCIntegrationCountrySerializer(instance.country).data}


class HMRCIntegrationCountrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Country
        fields = (
            "id",
            "name",
        )
        read_only_fields = fields


class HMRCIntegrationGoodsOnApplicationSerializer(serializers.ModelSerializer):
    id = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()

    class Meta:
        model = GoodOnApplication
        fields = (
            "id",
            "description",
            "usage",
            "unit",
            "quantity",
            "licenced_quantity",
            "licenced_value",
        )
        read_only_fields = fields

    def get_id(self, instance):
        return str(instance.good.id)

    def get_description(self, instance):
        return instance.good.description


class HMRCIntegrationGoodsTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = GoodsType
        fields = (
            "id",
            "description",
            "usage",
        )
        read_only_fields = fields
