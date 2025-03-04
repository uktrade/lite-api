from api.application_manifests.base import BaseManifest


def test_has_feature():
    manifest = BaseManifest()
    manifest.features = {"my-feature": True, "my-other-feature": False}
    assert manifest.has_feature("my-feature")
    assert manifest.has_feature("my-other-feature") is False
    assert manifest.has_feature("my-unknown-feature") is False
