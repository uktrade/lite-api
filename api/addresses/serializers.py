from rest_framework import serializers

from api.addresses.models import Address
from api.conf.serializers import CountrySerializerField
from lite_content.lite_api.strings import Addresses
from api.static.countries.helpers import get_country


class AddressSerializer(serializers.ModelSerializer):
    """
    Used for serializing addresses
    """

    address = serializers.CharField(max_length=256, required=False, error_messages={"blank": Addresses.ADDRESS})
    address_line_1 = serializers.CharField(
        max_length=50, required=False, error_messages={"blank": Addresses.ADDRESS_LINE_1}
    )
    postcode = serializers.CharField(max_length=10, required=False, error_messages={"blank": Addresses.POSTCODE})
    city = serializers.CharField(max_length=50, required=False, error_messages={"blank": Addresses.CITY})
    region = serializers.CharField(max_length=50, required=False, error_messages={"blank": Addresses.REGION})
    country = CountrySerializerField(required=False)

    def validate(self, data):
        validated_data = super().validate(data)

        if "address" in validated_data and "address_line_1" in validated_data:
            raise serializers.ValidationError({"address": "Provide either address or address_line_1"})

        if "address" in validated_data and validated_data["country"] == get_country("GB"):
            raise serializers.ValidationError({"address": "You can't select GB"})

        if "address_line_1" in validated_data:
            validated_data["country"] = get_country("GB")

        return validated_data

    def to_representation(self, instance):
        repr_dict = super().to_representation(instance)
        if repr_dict["address_line_1"]:
            del repr_dict["address"]
        else:
            del repr_dict["address_line_1"]
            del repr_dict["address_line_2"]
            del repr_dict["postcode"]
            del repr_dict["city"]
            del repr_dict["region"]
        return repr_dict

    class Meta:
        model = Address
        fields = (
            "id",
            "address",
            "address_line_1",
            "address_line_2",
            "city",
            "region",
            "postcode",
            "country",
        )
