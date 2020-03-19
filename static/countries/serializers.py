from rest_framework import serializers

from flags.enums import FlagStatuses
from static.countries.models import Country


class CountrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Country
        fields = (
            "id",
            "name",
            "type",
            "is_eu",
        )


class CountryWithFlagsSerializer(CountrySerializer):
    flags = serializers.SerializerMethodField()

    def get_flags(self, instance):
        # When returning flags for a country to view we only want active flags,
        # from what I can see this serializer is only used to view data not save any
        return list(instance.flags.filter(status=FlagStatuses.ACTIVE).values("id", "name"))

    class Meta:
        model = Country
        fields = "__all__"
