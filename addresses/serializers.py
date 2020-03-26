from rest_framework import serializers

from addresses.models import Address
from conf.serializers import CountrySerializerField
from static.countries.helpers import get_country


class AddressSerializer(serializers.ModelSerializer):
    """
    Used for serializing addresses
    """

    address = serializers.CharField(max_length=256, required=False, error_messages={"blank": "Enter a valid address"})
    address_line_1 = serializers.CharField(
        max_length=50, required=False, error_messages={"blank": "Enter a real building and street name"}
    )
    postcode = serializers.CharField(max_length=10, required=False, error_messages={"blank": "Enter a real postcode"})
    city = serializers.CharField(max_length=50, required=False, error_messages={"blank": "Enter a real city"})
    region = serializers.CharField(max_length=50, required=False, error_messages={"blank": "Enter a real region"})
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

    # def validate_country(self, value):
    #     if value == get_country("GB"):
    #         raise serializers.ValidationError({"country": "Cant be GB!"})
    #     return value
