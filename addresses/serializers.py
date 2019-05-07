from rest_framework import serializers

from addresses.models import Address


class AddressSerializer(serializers.ModelSerializer):
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

    def update(self, instance, validated_data):
        instance.address_line_1 = validated_data.get('address_line_1', instance.address_line_1)
        instance.address_line_2 = validated_data.get('address_line_2', instance.address_line_2)
        instance.zip_code = validated_data.get('zip_code', instance.zip_code)
        instance.city = validated_data.get('city', instance.city)
        instance.state = validated_data.get('state', instance.state)
        instance.country = validated_data.get('country', instance.country)
        instance.save()
        return instance