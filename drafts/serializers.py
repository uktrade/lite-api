from rest_framework import serializers
from drafts.models import Draft


class DraftSerializer(serializers.ModelSerializer):
    class Meta:
        model = Draft
        fields = ('id',
                  'user_id',
                  'control_code',
                  'activity',
                  'destination',
                  'usage',
                  'created_at',
                  'last_modified_at')
