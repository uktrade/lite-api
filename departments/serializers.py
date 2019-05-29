from rest_framework import serializers

from departments.models import Department
from rest_framework.validators import UniqueValidator


class DepartmentSerializer(serializers.ModelSerializer):
    name = serializers.CharField(
        validators=[UniqueValidator(queryset=Department.objects.all(), lookup='iexact')],
        error_messages={'blank': 'Department name may not be blank',
                        'unique': 'Enter a name which is not already in use by another department'})

    class Meta:
        model = Department
        fields = ('id',
                  'name')

    def update(self, instance, validated_data):
        """
        Update and return an existing `Application` instance, given the validated data.
        """
        instance.name = validated_data.get('name', instance.name)
        instance.save()
        return instance
