from rest_framework import serializers

from enumchoicefield import EnumChoiceField
from rest_framework.relations import PrimaryKeyRelatedField


from applications.models import Application, ApplicationStatus, GoodOnApplication, Site, SiteOnApplication, \
    LicenceType, ExportType

from applications.models import Application, ApplicationStatus, \
    GoodOnApplication, LicenceType, ExportType
from goods.serializers import GoodSerializer
from organisations.serializers import SiteViewSerializer


class ChoiceField(serializers.ChoiceField):

    def to_representation(self, obj):
        return self._choices[obj]


class GoodOnApplicationViewSerializer(serializers.ModelSerializer):
    good = GoodSerializer(read_only=True)

    class Meta:
        model = GoodOnApplication
        fields = ('id',
                  'good',
                  'quantity',
                  'unit',
                  'value')


class ApplicationBaseSerializer(serializers.ModelSerializer):
    created_at = serializers.DateTimeField(format="%Y-%m-%dT%H:%M:%SZ", read_only=True)
    last_modified_at = serializers.DateTimeField(format="%Y-%m-%dT%H:%M:%SZ", read_only=True)
    submitted_at = serializers.DateTimeField(format="%Y-%m-%dT%H:%M:%SZ", read_only=True)
    goods = GoodOnApplicationViewSerializer(many=True, read_only=True)
    status = serializers.CharField() # Doesnt validate yet
    licence_type = serializers.ChoiceField([(tag.name, tag.value) for tag in LicenceType],
                                           error_messages={
                                               'required': 'Select which type of licence you want to apply for.'})
    export_type = serializers.ChoiceField([(tag.name, tag.value) for tag in ExportType],
                                          error_messages={
                                              'required': 'Select if you want to apply for a temporary or permanent '
                                                          'licence.'})
    reference_number_on_information_form = serializers.CharField()

    class Meta:
        model = Application
        fields = ('id',
                  'name',
                  'activity',
                  'usage',
                  'goods',
                  'created_at',
                  'last_modified_at',
                  'submitted_at',
                  'status',
                  'licence_type',
                  'export_type',
                  'reference_number_on_information_form',)


class ApplicationUpdateSerializer(ApplicationBaseSerializer):
    name = serializers.CharField()
    usage = serializers.CharField()
    activity = serializers.CharField()
    status = serializers.CharField() # Doesnt validate yet
    licence_type = serializers.ChoiceField([(tag.name, tag.value) for tag in LicenceType],
                                           error_messages={
                                               'required': 'Select which type of licence you want to apply for.'})
    export_type = serializers.ChoiceField([(tag.name, tag.value) for tag in ExportType],
                                          error_messages={
                                              'required': 'Select if you want to apply for a temporary or permanent '
                                                          'licence.'})
    reference_number_on_information_form = serializers.CharField()

    def update(self, instance, validated_data):
        """
        Update and return an existing `Application` instance, given the validated data.
        """
        instance.name = validated_data.get('name', instance.name)
        instance.activity = validated_data.get('activity', instance.activity)
        instance.usage = validated_data.get('usage', instance.usage)
        instance.status = validated_data.get('status', instance.status)
        instance.licence_type = validated_data.get('licence_type', instance.licence_type)
        instance.export_type = validated_data.get('export_type', instance.export_type)
        instance.reference_number_on_information_form = validated_data.get(
            'reference_number_on_information_form', instance.reference_number_on_information_form)
        instance.save()
        return instance


class SiteOnApplicationBaseSerializer(serializers.ModelSerializer):
    application = PrimaryKeyRelatedField(queryset=Application.objects.all())
    site = PrimaryKeyRelatedField(queryset=Site.objects.all())

    class Meta:
        model = SiteOnApplication
        fields = ('id',
                  'site',
                  'application')


class SiteOnApplicationViewSerializer(serializers.ModelSerializer):
    site = SiteViewSerializer(read_only=True, many=True)
    application = ApplicationBaseSerializer(read_only=True)

    class Meta:
        model = SiteOnApplication
        fields = ('id',
                  'site',
                  'application')
