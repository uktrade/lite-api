from rest_framework import serializers
from rest_framework.relations import PrimaryKeyRelatedField

from applications.serializers import ApplicationBaseSerializer
from cases.models import Case, CaseNote
from gov_users.models import GovUser
from queues.models import Queue


class CaseSerializer(serializers.ModelSerializer):
    application = ApplicationBaseSerializer(read_only=True)

    class Meta:
        model = Case
        fields = ('id', 'application')


class CaseDetailSerializer(CaseSerializer):
    queues = PrimaryKeyRelatedField(many=True, queryset=Queue.objects.all())
    users = PrimaryKeyRelatedField(many=True, queryset=GovUser.objects.all())

    class Meta:
        model = Case
        fields = ('id', 'application', 'queues', 'users')


class CaseNoteSerializer(serializers.ModelSerializer):
    text = serializers.CharField(min_length=2, max_length=2200)
    case = PrimaryKeyRelatedField(queryset=Case.objects.all())
    user = PrimaryKeyRelatedField(queryset=GovUser.objects.all())
    created_at = serializers.DateTimeField(read_only=True)

    class Meta:
        model = CaseNote
        fields = ('id', 'text', 'case', 'user', 'created_at')
