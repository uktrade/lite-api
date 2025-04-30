from api.applications.application_manifest import ApplicationManifest
from api.cases.enums import ApplicationFeatures


def test_has_feature():
    manifest = ApplicationManifest()
    assert manifest.has_feature(ApplicationFeatures.LICENCE_ISSUE) is True
    assert manifest.has_feature(ApplicationFeatures.ROUTE_TO_COUNTERSIGNING_QUEUES) is True
