from rest_framework import serializers


def validate_field(data, field_name, error, required=False):
    is_field_present = field_name in data

    # Only validate the field if it is present in data
    if is_field_present:
        field_value = data.get(field_name)

        # Raise an error if the field_value is falsy but not False (boolean fields may have a field_value of False)
        if not field_value and field_value is not False:
            raise serializers.ValidationError({field_name: error})

        return field_value

    # Raise an error if the field is required but is not present in data
    if required:
        raise serializers.ValidationError({field_name: error})
