from api.cases.enums import ApplicationFeatures
from api.f680.application_manifest import F680ApplicationManifest


def test_has_feature():
    manifest = F680ApplicationManifest()
    assert manifest.has_feature(ApplicationFeatures.LICENCE_ISSUE) is False
