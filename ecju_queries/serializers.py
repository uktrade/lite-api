from rest_framework import serializers

from cases.models import Case
from ecju_queries.models import EcjuQuery
from users.models import GovUser


class EcjuQuerySerializer(serializers.ModelSerializer):
    class Meta:
        model = EcjuQuery
        fields = ('id',
                  'question',
                  'response',
                  'case',)


class EcjuQueryCreateSerializer(serializers.ModelSerializer):
    """
    Create specific serializer, which does not take a response as gov users don't respond to their own queries!
    """
    question = serializers.CharField(max_length=5000, allow_blank=False, allow_null=False)
    case = serializers.PrimaryKeyRelatedField(queryset=Case.objects.all())

    class Meta:
        model = EcjuQuery
        fields = ('id',
                  'question',
                  'case',
                  'raised_by_user',)
