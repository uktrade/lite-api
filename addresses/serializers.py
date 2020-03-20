from rest_framework import serializers

from addresses.models import Address, ForeignAddress
from conf.serializers import CountrySerializerField
from static.countries.helpers import get_country
from static.countries.serializers import CountrySerializer


class AddressSerializer(serializers.ModelSerializer):
    """
    Used for serializing addresses
    """

    address_line_1 = serializers.CharField(error_messages={"blank": "Enter a real building and street name"})
    postcode = serializers.CharField(max_length=10, error_messages={"blank": "Enter a real postcode"})
    city = serializers.CharField(error_messages={"blank": "Enter a real city"})
    region = serializers.CharField(error_messages={"blank": "Enter a real region"})
    country = CountrySerializer()

    class Meta:
        model = Address
        fields = (
            "id",
            "address_line_1",
            "address_line_2",
            "city",
            "region",
            "postcode",
            "country",
        )


class ForeignAddressSerializer(serializers.ModelSerializer):
    """
    Used for serializing foreign addresses
    """

    address = serializers.CharField(error_messages={"blank": "Enter a real building and street name"})
    country = CountrySerializer()

    class Meta:
        model = ForeignAddress
        fields = (
            "id",
            "address",
            "country",
        )
