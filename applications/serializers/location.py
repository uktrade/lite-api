from rest_framework import serializers
from rest_framework.relations import PrimaryKeyRelatedField

from applications.models import BaseApplication, SiteOnApplication, ExternalLocationOnApplication
from organisations.models import Site, ExternalLocation
from organisations.serializers import SiteViewSerializer


class SiteOnApplicationCreateSerializer(serializers.ModelSerializer):
    application = PrimaryKeyRelatedField(queryset=BaseApplication.objects.all())
    site = PrimaryKeyRelatedField(queryset=Site.objects.all())

    class Meta:
        model = SiteOnApplication
        fields = ('id',
                  'site',
                  'application',)


class SiteOnApplicationViewSerializer(serializers.ModelSerializer):
    site = SiteViewSerializer(read_only=True, many=True)
    # application = BaseApplicationSerializer(read_only=True)

    class Meta:
        model = SiteOnApplication
        fields = ('id',
                  'site',
                  'application',)


class ExternalLocationOnApplicationSerializer(serializers.ModelSerializer):
    application = PrimaryKeyRelatedField(queryset=BaseApplication.objects.all())
    external_location = PrimaryKeyRelatedField(queryset=ExternalLocation.objects.all())

    class Meta:
        model = ExternalLocationOnApplication
        fields = ('id',
                  'external_location',
                  'application',)