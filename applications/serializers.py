from rest_framework import serializers
from applications.models import Application


class ApplicationSerializer(serializers.ModelSerializer):
    created_at = serializers.DateTimeField(format="%Y-%m-%dT%H:%M:%SZ")
    last_modified_at = serializers.DateTimeField(format="%Y-%m-%dT%H:%M:%SZ")

    class Meta:
        model = Application
        fields = ('id',
                  'user_id',
                  'control_code',
                  'activity',
                  'destination',
                  'usage',
                  'created_at',
                  'last_modified_at')
