from rest_framework import serializers

from static.statuses.models import CaseStatus


class CaseStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = CaseStatus
        fields = (
            "id",
            "status",
            "priority",
        )
