from rest_framework import serializers

from addresses.models import Address


class AddressSerializer(serializers.ModelSerializer):
    address_line_1 = serializers.CharField()
    postcode = serializers.CharField(max_length=10)
    city = serializers.CharField()
    region = serializers.CharField()
    country = serializers.CharField()

    class Meta:
        model = Address
        fields = ('id',
                  'address_line_1',
                  'address_line_2',
                  'postcode',
                  'city',
                  'region',
                  'country')


class AddressUpdateSerializer(serializers.ModelSerializer):
    address_line_1 = serializers.CharField()
    postcode = serializers.CharField(max_length=10)
    city = serializers.CharField()
    region = serializers.CharField()
    country = serializers.CharField()

    class Meta:
        model = Address
        fields = ('id',
                  'address_line_1',
                  'address_line_2',
                  'postcode',
                  'city',
                  'region',
                  'country')

    def update(self, instance, validated_data):
        instance.address_line_1 = validated_data.get('address_line_1',
                                                     instance.address_line_1)
        instance.address_line_2 = validated_data.get('address_line_2',
                                                     instance.address_line_2)
        instance.postcode = validated_data.get('postcode', instance.postcode)
        instance.city = validated_data.get('city', instance.city)
        instance.region = validated_data.get('region', instance.region)
        instance.country = validated_data.get('country', instance.country)
        instance.save()
        return instance
