from rest_framework import serializers

from addresses.models import Address
from conf.serializers import CountrySerializerField


class AddressSerializer(serializers.ModelSerializer):
    """
    Used for serializing addresses
    """
    address_line_1 = serializers.CharField(error_messages={'blank': 'Enter a real building and street name'})
    postcode = serializers.CharField(max_length=10,
                                     error_messages={'blank': 'Enter a real postcode'})
    city = serializers.CharField(error_messages={'blank': 'Enter a real city'})
    region = serializers.CharField(error_messages={'blank': 'Enter a real region'})
    country = CountrySerializerField()

    class Meta:
        model = Address
        fields = ('id',
                  'address_line_1',
                  'address_line_2',
                  'city',
                  'region',
                  'postcode',
                  'country')
