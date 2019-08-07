from rest_framework import serializers

from cases.models import Case
from ecju_queries.models import EcjuQuery


class EcjuQuerySerializer(serializers.ModelSerializer):
    question = serializers.CharField(max_length=5000, allow_blank=False, allow_null=False)
    response = serializers.CharField(max_length=5000, required=False)
    case = serializers.PrimaryKeyRelatedField(queryset=Case.objects.all())

    class Meta:
        model = EcjuQuery
        fields = ('id',
                  'question',
                  'response',
                  'case',)
