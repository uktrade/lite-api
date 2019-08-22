from rest_framework import serializers

from addresses.models import Address
from conf.serializers import PrimaryKeyRelatedSerializerField
from content_strings.strings import get_string
from static.countries.models import Country
from static.countries.serializers import CountrySerializer


class AddressSerializer(serializers.ModelSerializer):
    """
    Used for serializing addresses
    """
    address_line_1 = serializers.CharField(error_messages={'blank': 'Enter a real building and street name'})
    postcode = serializers.CharField(max_length=10,
                                     error_messages={'blank': 'Enter a real postcode'})
    city = serializers.CharField(error_messages={'blank': 'Enter a real city'})
    region = serializers.CharField(error_messages={'blank': 'Enter a real region'})
    country = PrimaryKeyRelatedSerializerField(queryset=Country.objects.all(),
                                               serializer=CountrySerializer,
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
