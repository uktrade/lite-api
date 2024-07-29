from rest_framework import serializers

from api.applications.models import StandardApplication


def get_original_application(obj):
    if not obj.amendment_of:
        return obj
    return get_original_application(obj.amendment_of)


def get_last_application(obj):
    if not obj.superseded_by:
        return obj
    return get_last_application(obj.superseded_by)


class ApplicationSerializer(serializers.ModelSerializer):
    created_at = serializers.SerializerMethodField(required=False)
    submitted_at = serializers.SerializerMethodField(required=False)
    closed_at = serializers.SerializerMethodField(required=False)
    closed_status = serializers.SerializerMethodField(required=False)

    class Meta:
        model = StandardApplication
        fields = (
            "id",
            "created_at",
            "submitted_at",
            "closed_at",
            "closed_status",
        )

    def get_created_at(self, application):
        application = get_original_application(application)
        return application.created_at

    def get_submitted_at(self, application):
        application = get_original_application(application)
        return application.first_submitted_at

    def get_closed_at(self, application):
        application = get_last_application(application)
        return application.closed_at

    def get_closed_status(self, application):
        application = get_last_application(application)
        return application.closed_status
