from rest_framework import serializers


from .models import RegimeEntry


class RegimeEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = RegimeEntry
        fields = ["pk", "name"]
