from rest_framework import serializers

from addresses.models import Address
from content_strings.strings import get_string
from static.countries.models import Country


class AddressSerializer(serializers.ModelSerializer):
    """
    Used for serializing addresses
    """
    address_line_1 = serializers.CharField()
    postcode = serializers.CharField(max_length=10)
    city = serializers.CharField()
    region = serializers.CharField()
    country = serializers.PrimaryKeyRelatedField(queryset=Country.objects.all(),
                                                 error_messages={'null': get_string('address.null_country')})

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


class AddressCountrylessSerializer(serializers.ModelSerializer):
    address_line_1 = serializers.CharField()
    postcode = serializers.CharField(max_length=10)
    city = serializers.CharField()
    region = serializers.CharField()
    # TODO: Add country primary key back
    # This was removed as Django seemingly has issues deserializing it
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
