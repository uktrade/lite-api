from rest_framework import serializers

from .models import SurveyResponse


class SurveyResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = SurveyResponse
        fields = fields = ("id", "satisfaction_rating", "case_type", "user_journey")


class SurveyResponseUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = SurveyResponse
        fields = "__all__"
