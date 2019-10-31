from rest_framework import serializers

from applications.models import OpenApplication
from applications.serializers.generic_application import GenericApplicationCreateSerializer, \
    GenericApplicationUpdateSerializer
from goodstype.models import GoodsType
from goodstype.serializers import FullGoodsTypeSerializer
from static.countries.models import Country
from static.countries.serializers import CountrySerializer


class OpenApplicationViewSerializer(serializers.ModelSerializer):
    destinations = serializers.SerializerMethodField()
    goods_types = serializers.SerializerMethodField()

    class Meta:
        model = OpenApplication
        fields = [
            'destinations',
            'goods_types',
        ]

    def get_destinations(self, application):
        countries = Country.objects.filter(countries_on_application__application=application)
        serializer = CountrySerializer(countries, many=True)
        return {'type': 'countries', 'data': serializer.data}

    def get_goods_types(self, application):
        goods_types = GoodsType.objects.filter(application=application)
        serializer = FullGoodsTypeSerializer(goods_types, many=True)
        return serializer.data


class OpenApplicationCreateSerializer(GenericApplicationCreateSerializer):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.initial_data['organisation'] = self.context.id

    class Meta:
        model = OpenApplication
        fields = ['id',
                  'name',
                  'application_type',
                  'export_type',
                  'have_you_been_informed',
                  'reference_number_on_information_form',
                  'organisation']


class OpenApplicationUpdateSerializer(GenericApplicationUpdateSerializer):
    class Meta:
        model = OpenApplication
        fields = ['id',
                  'name',
                  'application_type',
                  'export_type',
                  'have_you_been_informed',
                  'reference_number_on_information_form',
                  'organisation']
