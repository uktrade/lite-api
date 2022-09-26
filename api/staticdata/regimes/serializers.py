from rest_framework import serializers


from .models import (
    Regime,
    RegimeEntry,
    RegimeSubsection,
)


class RegimeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Regime
        fields = [
            "pk",
            "name",
        ]


class RegimeSubsectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = RegimeSubsection
        fields = [
            "pk",
            "name",
            "regime",
        ]

    regime = RegimeSerializer()


class RegimeEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = RegimeEntry
        fields = [
            "pk",
            "name",
            "subsection",
        ]

    subsection = RegimeSubsectionSerializer()
