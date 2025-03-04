from api.applications.models import StandardApplication
from api.applications.serializers.standard_application import StandardApplicationViewSerializer
from api.cases.enums import CaseTypeSubTypeEnum, ApplicationFeatures
from api.f680.models import F680Application
from api.f680.caseworker.serializers import F680ApplicationSerializer


class BaseManifest:
    caseworker_serializers = {}
    model_class = None
    features = {}

    def has_feature(self, feature):
        return self.features.get(feature, False)


class StandardApplicationManifest(BaseManifest):
    model_class = StandardApplication
    caseworker_serializers = {"view": StandardApplicationViewSerializer}
    features = {ApplicationFeatures.LICENCE_ISSUE: True}


class F680ApplicationManifest(BaseManifest):
    model_class = F680Application
    caseworker_serializers = {"view": F680ApplicationSerializer}
    features = {ApplicationFeatures.LICENCE_ISSUE: False}


# TODO: Make it so that each application django app defines/registers its own
# manifest, instead of doing it all in this file. Probably using a decorator
class ManifestRegistry:

    def __init__(self):
        self.manifests = {}

    def register(self, application_type, manifest):
        self.manifests[application_type] = manifest

    def get_manifest(self, application_type):
        return self.manifests[application_type]


application_manifest_registry = ManifestRegistry()
application_manifest_registry.register(CaseTypeSubTypeEnum.STANDARD, StandardApplicationManifest())
application_manifest_registry.register(CaseTypeSubTypeEnum.F680, F680ApplicationManifest())
