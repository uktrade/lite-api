from rest_framework import serializers

from cases.serializers import CaseSerializer
from queues.models import Queue


class QueueSerializer(serializers.ModelSerializer):
    cases = CaseSerializer(many=True, read_only=True)
    team = serializers.SlugRelatedField(many=False,
                                        read_only=True,
                                        slug_field='name'
                                        )

    class Meta:
        model = Queue
        fields = ('id',
                  'name',
                  'cases',
                  'team')
