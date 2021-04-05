import re
import string

from rest_framework import serializers

from api.addresses.models import Address
from api.core.serializers import CountrySerializerField
from lite_content.lite_api.strings import Addresses
from api.staticdata.countries.helpers import get_country


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
    phone_number = serializers.CharField(required=True, allow_blank=True)
    website = serializers.CharField(required=False, allow_blank=True)

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
            "phone_number",
            "website",
        )

    def validate_postcode(self, value):
        """
        Taken from django-localflavor
        https://github.com/django/django-localflavor/blob/master/localflavor/gb/forms.py
        """
        outcode_pattern = "[A-PR-UWYZ]([0-9]{1,2}|([A-HIK-Y][0-9](|[0-9]|[ABEHMNPRVWXY]))|[0-9][A-HJKSTUW])"
        incode_pattern = "[0-9][ABD-HJLNP-UW-Z]{2}"
        postcode_regex = re.compile(r"^(GIR 0AA|%s %s)$" % (outcode_pattern, incode_pattern))
        space_regex = re.compile(r" *(%s)$" % incode_pattern)

        postcode = value.upper().strip()
        # Put a single space before the incode (second part).
        postcode = space_regex.sub(r" \1", postcode)

        if not postcode_regex.search(postcode):
            raise serializers.ValidationError(Addresses.POSTCODE)
        return value

    def validate(self, data):
        validated_data = super().validate(data)

        if "address" in validated_data and "address_line_1" in validated_data:
            raise serializers.ValidationError({"address": "Provide either address or address_line_1"})

        if "address" in validated_data and validated_data["country"] == get_country("GB"):
            raise serializers.ValidationError({"address": "You can't select GB"})

        if "address_line_1" in validated_data:
            validated_data["country"] = get_country("GB")

        if "phone_number" in validated_data:
            error = (
                "Enter an organisation phone number"
                if self.context.get("commercial", "commercial")
                else "Enter a phone number"
            )
            if validated_data["phone_number"] == "":
                raise serializers.ValidationError({"phone_number": error})

            allowed_chars = set(string.digits + "+-/()[]x ")
            if not (set(validated_data["phone_number"]) <= allowed_chars):
                raise serializers.ValidationError({"phone_number": error})

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
