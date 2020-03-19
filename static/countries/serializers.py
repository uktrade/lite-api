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
        if self.context.get("active_flags"):
            return list(instance.flags.filter(status=FlagStatuses.ACTIVE).values("id", "name"))
        else:
            return list(instance.flags.values("id", "name"))

    class Meta:
        model = Country
        fields = "__all__"
