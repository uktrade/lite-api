import json

from actstream.models import Action
from rest_framework import serializers

from audit_trail.constants import Verb


class ActivitySerializer(serializers.ModelSerializer):
    """
    Serializer to serialize Action to current format for CaseActivity
    """
    user = serializers.SerializerMethodField()
    created_at = serializers.SerializerMethodField()
    text = serializers.SerializerMethodField()

    class Meta:
        model = Action
        fields = ("id", "created_at", "user", "text")

    def get_user(self, instance):
        return {
            "first_name": instance.actor.first_name,
            "last_name": instance.actor.last_name,
        }

    def get_created_at(self, instance):
        return instance.timestamp

    def get_text(self, instance):
        verb = Verb(instance.verb)

        if verb in [Verb.ADDED_QUEUES, Verb.REMOVED_QUEUES]:
            # Special case for case queue management audit
            # Queues are many objects so `data` json field
            # is used to reference the Queue names.
            data = json.loads(instance.data)
            return f"{instance.verb}: {', '.join([q for q in data['payload']['queues']])}"

        return f"{instance.verb}"
