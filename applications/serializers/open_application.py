from datetime import datetime, timezone

from rest_framework import serializers
from rest_framework.fields import CharField

from applications.models import OpenApplication
from applications.serializers.generic_application import GenericApplicationCreateSerializer, \
    GenericApplicationUpdateSerializer, GenericApplicationListSerializer
from content_strings.strings import get_string
from goodstype.models import GoodsType
from goodstype.serializers import FullGoodsTypeSerializer
from organisations.models import Site, ExternalLocation
from organisations.serializers import SiteViewSerializer, ExternalLocationSerializer
from static.countries.models import Country
from static.countries.serializers import CountrySerializer


class OpenApplicationViewSerializer(GenericApplicationListSerializer):
    destinations = serializers.SerializerMethodField()
    goods_types = serializers.SerializerMethodField()
    goods_locations = serializers.SerializerMethodField()

    class Meta:
        model = OpenApplication
        fields = GenericApplicationListSerializer.Meta.fields + [
            'destinations',
            'goods_types',
            'have_you_been_informed',
            'reference_number_on_information_form',
            'goods_locations'
        ]

    def get_destinations(self, application):
        countries = Country.objects.filter(countries_on_application__application=application)
        serializer = CountrySerializer(countries, many=True)
        return {'type': 'countries', 'data': serializer.data}

    def get_goods_types(self, application):
        goods_types = GoodsType.objects.filter(application=application)
        serializer = FullGoodsTypeSerializer(goods_types, many=True)
        return serializer.data

    def get_goods_locations(self, application):
        sites = Site.objects.filter(sites_on_application__application=application)

        if sites:
            serializer = SiteViewSerializer(sites, many=True)
            return {'type': 'sites', 'data': serializer.data}

        external_locations = ExternalLocation.objects.filter(
            external_locations_on_application__application=application)

        if external_locations:
            serializer = ExternalLocationSerializer(external_locations, many=True)
            return {'type': 'external_locations', 'data': serializer.data}

        return {}


class OpenApplicationCreateSerializer(GenericApplicationCreateSerializer):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.initial_data['organisation'] = self.context.id

    class Meta:
        model = OpenApplication
        fields = [
            'id',
            'name',
            'application_type',
            'export_type',
            'have_you_been_informed',
            'reference_number_on_information_form',
            'organisation'
        ]


class OpenApplicationUpdateSerializer(GenericApplicationUpdateSerializer):
    name = CharField(max_length=100,
                     required=True,
                     allow_blank=False,
                     allow_null=False,
                     error_messages={'blank': get_string('goods.error_messages.ref_name')})
    reference_number_on_information_form = CharField(max_length=100,
                                                     required=False,
                                                     allow_blank=True,
                                                     allow_null=True)

    class Meta:
        model = OpenApplication
        fields = GenericApplicationUpdateSerializer.Meta.fields + [
            'have_you_been_informed',
            'reference_number_on_information_form',
        ]

    def update(self, instance, validated_data):
        instance.have_you_been_informed = validated_data.get('have_you_been_informed', instance.have_you_been_informed)
        if instance.have_you_been_informed == 'yes':
            instance.reference_number_on_information_form = validated_data.get(
                'reference_number_on_information_form', instance.reference_number_on_information_form)
        else:
            instance.reference_number_on_information_form = None
        instance.last_modified_at = datetime.now(timezone.utc)
        instance = super().update(instance, validated_data)
        return instance
