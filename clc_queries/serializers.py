from rest_framework import serializers

from clc_queries.models import ClcQuery
from goods.serializers import FullGoodSerializer
from static.statuses.models import CaseStatus


class ClcQuerySerializer(serializers.ModelSerializer):
    good = FullGoodSerializer(read_only=True)
    organisation_name = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    submitted_at = serializers.DateTimeField(read_only=True)

    class Meta:
        model = ClcQuery
        fields = (
            'id',
            'details',
            'good',
            'status',
            'organisation_name',
            'submitted_at')

    def get_organisation_name(self, instance):
        return instance.good.organisation.name

    def get_status(self, application):
        return application.status.status


class ClcQueryUpdateSerializer(serializers.ModelSerializer):
    status = serializers.PrimaryKeyRelatedField(queryset=CaseStatus.objects.all())

    class Meta:
        model = ClcQuery
        fields = (
            'id',
            'status')

    # pylint: disable = W0221
    def update(self, instance, partial):
        instance.status = partial.get('status', instance.status)
        instance.save()
        return instance
