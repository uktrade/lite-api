from rest_framework import serializers

from applications.models import BaseApplication, ApplicationDenialReason
from static.denial_reasons.models import DenialReason


class DenialReasonSerializer(serializers.ModelSerializer):
    id = serializers.CharField()

    class Meta:
        model = DenialReason
        fields = ("id",)


class ApplicationDenialReasonViewSerializer(serializers.ModelSerializer):
    reasons = DenialReasonSerializer(read_only=False, many=True)

    class Meta:
        model = ApplicationDenialReason
        fields = (
            "id",
            "reason_details",
            "reasons",
        )


class ApplicationDenialReasonCreateSerializer(serializers.ModelSerializer):
    reason_details = serializers.CharField(max_length=2200, required=False, allow_blank=True, allow_null=True)
    application = serializers.PrimaryKeyRelatedField(queryset=BaseApplication.objects.all())

    class Meta:
        model = ApplicationDenialReason
        fields = (
            "reason_details",
            "application",
        )

    def create(self, validated_data):
        if self.initial_data["reasons"]:
            application_denial_reason = ApplicationDenialReason.objects.create(**validated_data)
            application_denial_reason.reasons.set(self.initial_data["reasons"])
            application_denial_reason.save()

            return application_denial_reason
        else:
            raise serializers.ValidationError("Select at least one denial reason")
