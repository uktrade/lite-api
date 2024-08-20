from rest_framework import serializers

from api.applications.models import StandardApplication


def get_original_application(obj):
    if not obj.amendment_of:
        return obj
    return get_original_application(obj.amendment_of)


class LicenceStatusSerializer(serializers.Serializer):
    name = serializers.CharField(source="*")


class LicenceDecisionTypeSerializer(serializers.Serializer):
    name = serializers.CharField(source="*")


class SIELApplicationSerializer(serializers.ModelSerializer):
    id = serializers.SerializerMethodField(required=False)

    class Meta:
        model = StandardApplication
        fields = ("id", "status")

    def get_id(self, application):
        application = get_original_application(application)
        return application.pk
