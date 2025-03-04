import pytest
from unittest import mock

from api.cases.enums import ApplicationFeatures
from api.cases.application_manifest import (
    ManifestRegistry,
    BaseManifest,
    F680ApplicationManifest,
    StandardApplicationManifest,
)


pytestmark = pytest.mark.django_db


class TestManifestRegistry:

    def test_register(self):
        registry = ManifestRegistry()
        mock_manifest = mock.Mock()
        registry.register("some_application_type", mock_manifest)
        assert registry.manifests == {"some_application_type": mock_manifest}

    def test_get_manifest_success(self):
        registry = ManifestRegistry()
        mock_manifest = mock.Mock()
        registry.manifests = {"some_application_type": mock_manifest}
        assert registry.get_manifest("some_application_type") == mock_manifest

    def test_get_manifest_manifest_missing(self):
        registry = ManifestRegistry()
        with pytest.raises(KeyError):
            registry.get_manifest("some_application_type")


class TestBaseManifest:

    def test_has_feature(self):
        manifest = BaseManifest()
        manifest.features = {"my-feature": True, "my-other-feature": False}
        assert manifest.has_feature("my-feature")
        assert manifest.has_feature("my-other-feature") is False
        assert manifest.has_feature("my-unknown-feature") is False


class TestStandardApplicationManifest:

    def test_has_feature(self):
        manifest = StandardApplicationManifest()
        assert manifest.has_feature(ApplicationFeatures.LICENCE_ISSUE) is True


class TestF680ApplicationManifest:

    def test_has_feature(self):
        manifest = F680ApplicationManifest()
        assert manifest.has_feature(ApplicationFeatures.LICENCE_ISSUE) is False
