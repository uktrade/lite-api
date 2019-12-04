import json

from audit_trail.models import Audit
from rest_framework import serializers

from audit_trail.constants import Verb


class AuditSerializer(serializers.ModelSerializer):
    """
    Serializer to serialize Action to current format for CaseActivity
    """
    user = serializers.SerializerMethodField()
    text = serializers.SerializerMethodField()
    additional_text = serializers.SerializerMethodField()

    class Meta:
        model = Audit
        fields = ("id", "created_at", "user", "text", "additional_text")

    def get_user(self, instance):
        return {
            "first_name": instance.actor.first_name,
            "last_name": instance.actor.last_name,
        }

    def get_text(self, instance):
        verb = Verb(instance.verb)

        if verb in [Verb.ADDED_QUEUES, Verb.REMOVED_QUEUES]:
            # Special case for case queue management audit
            # Queues are many objects so `data` json field
            # is used to reference the Queue names.
            queues = sorted([q for q in instance.payload['queues']])
            return f"{instance.verb}: {', '.join(queues)}"

        if verb in [Verb.ADDED_FLAGS, Verb.REMOVED_FLAGS]:
            from cases.models import Case
            if isinstance(instance.action_object, Case):
                return f"{instance.verb} on case: {instance.action_object.id}"
            else:
                return f"{instance.verb} on good: {instance.action_object.description}"

        if verb == Verb.ADDED_ECJU:
            return f"added an ECJU Query: {instance.action_object.question}"

        if verb == Verb.UPLOADED_DOCUMENT:
            return f"uploaded case document: {instance.payload['file_name']}"

        if verb == Verb.UPDATED_CONTROL_CODE:
            good = instance.payload['good']
            clc = instance.payload['control_code']
            return f'good was reviewed: {good["name"]} control code changed from {clc["old"]} to {clc["new"]}',

        if verb == Verb.UPDATED_STATUS:
            return f"updated status to {instance.payload['status']}"

        if verb == Verb.CLC_RESPONSE:
            return f"responded to the case"

        return f"{instance.verb}:"

    def get_additional_text(self, instance):
        verb = Verb(instance.verb)

        if verb == Verb.ADDED_NOTE:
            return f"{instance.payload['note']}"

        if verb in [Verb.ADDED_FLAGS, Verb.REMOVED_FLAGS]:
            flag_names = sorted([f['name'] for f in instance.payload['flags']])
            return f"{', '.join(flag_names)}"

        return ""
