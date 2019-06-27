from rest_framework import serializers
from rest_framework.relations import PrimaryKeyRelatedField

from applications.serializers import ApplicationBaseSerializer
from cases.models import Case, CaseNote
from gov_users.models import GovUser


class CaseSerializer(serializers.ModelSerializer):
    application = ApplicationBaseSerializer(read_only=True)

    class Meta:
        model = Case
        fields = ('id', 'application')


class CaseDetailSerializer(CaseSerializer):
    queues = PrimaryKeyRelatedField(many=True, read_only=True)
    users = PrimaryKeyRelatedField(many=True, read_only=True)

    class Meta:
        model = Case
        fields = ('id', 'application', 'queues', 'users')

    def create(self, validated_data):
        queues = validated_data.pop('queues')
        # users = validated_data.pop('users')

        case = Case.objects.create(**validated_data)

        case.queues.set(*queues)
        # case.users.set(*users)
        return case

    def update(self, instance, validated_data):
        # queues = validated_data.pop('queues')
        # users = validated_data.pop('users')

        instance.queues.set(validated_data.get('queues'))
        # instance.users.set(validated_data.get('users'))

        instance.save()
        return instance


class CaseNoteSerializer(serializers.ModelSerializer):
    text = serializers.CharField(min_length=2, max_length=2200)
    case = PrimaryKeyRelatedField(queryset=Case.objects.all())
    user = PrimaryKeyRelatedField(queryset=GovUser.objects.all())
    created_at = serializers.DateTimeField(read_only=True)

    class Meta:
        model = CaseNote
        fields = ('id', 'text', 'case', 'user', 'created_at')
