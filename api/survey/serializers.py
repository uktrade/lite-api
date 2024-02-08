from rest_framework import serializers

from .models import Survey


class SurveySerializer(serializers.ModelSerializer):

    class Meta:
        model = Survey
        fields = "__all__"

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        return {"id": rep["id"], "recommendation": rep["recommendation"]}
