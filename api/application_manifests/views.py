from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from api.application_manifests.models import ApplicationManifestFeatures
from api.application_manifests.serializers import ApplicationManifestFeatureSerializer
from api.cases.enums import ApplicationFeatures
from api.core.authentication import GovAuthentication


class ApplicationManifestFeaturesViewSet(viewsets.ModelViewSet):
    authentication_classes = (GovAuthentication,)
    queryset = ApplicationManifestFeatures.objects.all()
    serializer_class = ApplicationManifestFeatureSerializer
    lookup_field = "case_type"

    @action(detail=True, methods=["patch"])
    def update_feature(self, request, case_type=None):
        instance = self.get_object()
        feature_name = request.data.get("feature_name")
        feature_value = request.data.get("feature_value")

        valid_features = {item.value for item in ApplicationFeatures}

        if feature_name not in valid_features:
            return Response({"error": f"Invalid feature name: {feature_name}"}, status=400)

        if not isinstance(feature_value, bool):
            return Response({"error": "Feature value must be boolean"}, status=400)

        settings = instance.features
        settings[feature_name] = feature_value
        instance.features = settings
        instance.save()

        return Response(self.get_serializer(instance).data)
