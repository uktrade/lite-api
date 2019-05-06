from rest_framework import serializers

from addresses.models import Address


class AddressBaseSerializer(serializers.ModelSerializer):
    address_line_1 = serializers.CharField()
    zip_code = serializers.CharField()
    city = serializers.CharField()
    state = serializers.CharField()
    country = serializers.CharField()

    class Meta:
        model = Address
        fields = ('id',
                  'address_line_1',
                  'address_line_2',
                  'zip_code',
                  'city',
                  'state',
                  'country')


class AddressViewSerializer(serializers.ModelSerializer):
    address_line_1 = serializers.CharField()
    zip_code = serializers.CharField()
    city = serializers.CharField()
    state = serializers.CharField()
    country = serializers.CharField()

    class Meta:
        model = Address
        fields = ('id',
                  'address_line_1',
                  'address_line_2',
                  'zip_code',
                  'city',
                  'state',
                  'country')


class AddressUpdateSerializer(serializers.ModelSerializer):
    address_line_1 = serializers.CharField()
    zip_code = serializers.CharField()
    city = serializers.CharField()
    state = serializers.CharField()
    country = serializers.CharField()

    class Meta:
        model = Address
        fields = ('id',
                  'address_line_1',
                  'address_line_2',
                  'zip_code',
                  'city',
                  'state',
                  'country')
