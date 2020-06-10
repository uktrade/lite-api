from rest_framework import serializers

from open_general_licences.models import OpenGeneralLicence
from organisations.models import Site


class OGLApplicationListSerializer(serializers.ModelSerializer):
    open_general_licence = serializers.PrimaryKeyRelatedField(queryset=OpenGeneralLicence.objects.all())
    site = serializers.PrimaryKeyRelatedField(queryset=Site.objects.all())


class OGLApplicationDetailSerializer(serializers.ModelSerializer):
    open_general_licence = serializers.PrimaryKeyRelatedField(queryset=OpenGeneralLicence.objects.all())
    site = serializers.PrimaryKeyRelatedField(queryset=Site.objects.all())
