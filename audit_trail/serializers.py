import logging
from copy import deepcopy

from rest_framework import serializers

from audit_trail.models import Audit
from audit_trail.payload import AuditType


class AuditSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    text = serializers.SerializerMethodField()
    additional_text = serializers.SerializerMethodField()

    class Meta:
        model = Audit
        fields = (
            "id",
            "created_at",
            "user",
            "text",
            "additional_text",
        )

    def get_user(self, instance):
        return {
            "first_name": instance.actor.first_name,
            "last_name": instance.actor.last_name,
        }

    def get_text(self, instance):
        try:
            verb = AuditType(instance.verb)
            payload = deepcopy(instance.payload)

            for key in payload:
                # If value is a list, join by comma.
                if isinstance(payload[key], list):
                    payload[key] = ", ".join(payload[key])

                # TODO: standardise payloads across all audits and remove below
                if key == "status" and "new" in payload[key]:
                    # Handle new payload format
                    payload[key] = payload[key]["new"]

            return verb.format(payload)
        except Exception as e:  # noqa
            logging.warning(f"Failed to get text for audit: {instance.id}")
            return ""

    def get_additional_text(self, instance):
        return instance.payload.get("additional_text", "")
