from api.applications.models import StandardApplication
from api.applications.serializers.standard_application import StandardApplicationViewSerializer
from api.application_manifests.base import BaseManifest
from api.application_manifests.registry import application_manifest_registry
from api.cases.enums import ApplicationFeatures, CaseTypeSubTypeEnum


@application_manifest_registry.register(CaseTypeSubTypeEnum.STANDARD)
class StandardApplicationManifest(BaseManifest):
    model_class = StandardApplication
    caseworker_serializers = {"view": StandardApplicationViewSerializer}
    features = {ApplicationFeatures.LICENCE_ISSUE: True}
