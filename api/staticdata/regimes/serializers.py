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
            "shortened_name",
            "subsection",
        ]

    subsection = RegimeSubsectionSerializer()


# Below serializers for DW use
class RegimesListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Regime
        fields = "__all__"


class RegimeSubsectionsListSerializer(serializers.ModelSerializer):
    class Meta:
        model = RegimeSubsection
        fields = "__all__"


class RegimeEntriesListSerializer(serializers.ModelSerializer):
    class Meta:
        model = RegimeEntry
        fields = "__all__"
