from rest_framework import serializers

from departments.models import Department
from rest_framework.validators import UniqueValidator


class DepartmentSerializer(serializers.ModelSerializer):
    name = serializers.CharField(
        max_length=50,
        validators=[UniqueValidator(queryset=Department.objects.all(), lookup='iexact',
                                    message='Enter a name which is not already in use by another department')],
        error_messages={'blank': 'Department name may not be blank'})

    class Meta:
        model = Department
        fields = ('id',
                  'name')

    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        instance.save()
        return instance
