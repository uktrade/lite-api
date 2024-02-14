from rest_framework import serializers

from .models import SurveyResponse


class SurveyResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = SurveyResponse
        fields = fields = (
            "id",
            "recommendation",
        )


class SurveyResponseUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = SurveyResponse
        fields = "__all__"
