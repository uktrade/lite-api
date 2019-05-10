from rest_framework import serializers

from applications.serializers import ApplicationBaseSerializer
from cases.models import Case


class CaseSerializer(serializers.ModelSerializer):
    application = ApplicationBaseSerializer(read_only=True)

    class Meta:
        model = Case
        fields = ('id', 'application')


class CaseNoteSerializer(serializers.ModelSerializer):

    class Meta:
        model = Case
        fields = ('id', 'application')
