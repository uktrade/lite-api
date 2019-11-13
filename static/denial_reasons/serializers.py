from rest_framework import serializers

from static.denial_reasons.models import DenialReason


class DenialReasonSerializer(serializers.ModelSerializer):
    class Meta:
        model = DenialReason
        fields = (
            "id",
            "deprecated",
        )
