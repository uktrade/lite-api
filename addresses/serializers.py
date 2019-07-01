from rest_framework import serializers

from addresses.models import Address
from static.countries.models import Country


class AddressSerializer(serializers.ModelSerializer):
    address_line_1 = serializers.CharField()
    postcode = serializers.CharField(max_length=10)
    city = serializers.CharField()
    region = serializers.CharField()
    country = serializers.PrimaryKeyRelatedField(queryset=Country.objects.all())

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


class AddressCountrylessSerializer(serializers.ModelSerializer):
    address_line_1 = serializers.CharField()
    postcode = serializers.CharField(max_length=10)
    city = serializers.CharField()
    region = serializers.CharField()
    # TODO: Add country primary key back
    # country = serializers.PrimaryKeyRelatedField(queryset=Country.objects.all())
    country = serializers.CharField(allow_blank=False, allow_null=False)

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
        # instance.country = validated_data.get('country', instance.country)
        instance.save()
        return instance
