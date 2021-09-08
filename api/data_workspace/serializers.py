from api.cases.models import EcjuQuery, CaseAssignment

from rest_framework import serializers
import api.cases.serializers as cases_serializers


class EcjuQuerySerializer(serializers.ModelSerializer):
    class Meta:
        model = EcjuQuery
        fields = "__all__"


class CaseAssignmentSerializer(cases_serializers.CaseAssignmentSerializer):
    # Like original, but with all fields
    class Meta:
        model = CaseAssignment
        fields = "__all__"
