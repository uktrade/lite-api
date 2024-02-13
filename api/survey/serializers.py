from rest_framework import serializers

from .models import SurveyResponse


class SurveyResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = SurveyResponse
        fields = "__all__"

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        return {"id": rep["id"], "recommendation": rep["recommendation"]}
