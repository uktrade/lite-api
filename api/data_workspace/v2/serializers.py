from rest_framework import serializers

from api.applications.models import StandardApplication
from api.cases.models import EcjuQuery


def get_original_application(obj):
    if not obj.amendment_of:
        return obj
    return get_original_application(obj.amendment_of)


def get_last_application(obj):
    if not obj.superseded_by:
        return obj
    return get_last_application(obj.superseded_by)


class ApplicationSerializer(serializers.ModelSerializer):
    id = serializers.SerializerMethodField(required=False)

    class Meta:
        model = StandardApplication
        fields = ("id",)

    def get_id(self, application):
        application = get_original_application(application)
        return application.pk


class RFISerializer(serializers.ModelSerializer):
    application_id = serializers.SerializerMethodField(required=False)
    closed_at = serializers.SerializerMethodField(required=False)

    class Meta:
        model = EcjuQuery
        fields = (
            "id",
            "application_id",
            "created_at",
            "closed_at",
        )

    def get_application_id(self, rfi):
        return get_original_application(rfi.case).pk

    def get_closed_at(self, rfi):
        return rfi.responded_at
