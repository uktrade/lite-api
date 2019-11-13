from rest_framework import serializers

from static.countries.models import Country


class CountrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Country
        fields = (
            "id",
            "name",
            "type",
        )
