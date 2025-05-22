from rest_framework import serializers

from api.cases.enums import ApplicationFeatures
from models import ApplicationManifestFeatures


class ApplicationManifestFeatureSerializer(serializers.ModelSerializer):
    class Meta:
        model = ApplicationManifestFeatures
        fields = (
            'case_type',
            'features'
        )

    @staticmethod
    def validate_features(value):
        valid_features = set(ApplicationFeatures.__members__.keys())
        provided_features = set(value.keys())

        invalid_features = provided_features - valid_features
        if invalid_features:
            raise serializers.ValidationError(
                f"Invalid Features: {', '.join(invalid_features)}"
            )
        for feature_name, feature_value in value.items():
            if not isinstance(feature_value, bool):
                raise serializers.ValidationError(
                    f"Feature '{feature_name}' must be a boolean value"
                )

        return value
