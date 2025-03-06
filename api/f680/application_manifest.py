from api.f680.models import F680Application
from api.f680.caseworker.serializers import F680ApplicationSerializer
from api.application_manifests.base import BaseManifest
from api.application_manifests.registry import application_manifest_registry
from api.cases.enums import ApplicationFeatures, CaseTypeSubTypeEnum


@application_manifest_registry.register(CaseTypeSubTypeEnum.F680)
class F680ApplicationManifest(BaseManifest):
    model_class = F680Application
    caseworker_serializers = {"view": F680ApplicationSerializer}
    features = {ApplicationFeatures.LICENCE_ISSUE: False}
