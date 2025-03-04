from api.applications.application_manifest import StandardApplicationManifest
from api.cases.enums import ApplicationFeatures


def test_has_feature():
    manifest = StandardApplicationManifest()
    assert manifest.has_feature(ApplicationFeatures.LICENCE_ISSUE) is True
