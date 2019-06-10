from rest_framework import serializers
from rest_framework.relations import PrimaryKeyRelatedField

from applications.serializers import ApplicationBaseSerializer
from cases.models import Case, CaseNote


class CaseSerializer(serializers.ModelSerializer):
    """
    Serializes cases
    """
    application = ApplicationBaseSerializer(read_only=True)

    class Meta:
        model = Case
        fields = ('id', 'application')


class CaseNoteSerializer(serializers.ModelSerializer):
    """
    Serializes case notes
    """
    text = serializers.CharField(min_length=2, max_length=2200)
    case = PrimaryKeyRelatedField(queryset=Case.objects.all())
    created_at = serializers.DateTimeField(format='%Y-%m-%dT%H:%M:%SZ', read_only=True)

    class Meta:
        model = CaseNote
        fields = ('id', 'case', 'text', 'created_at')
