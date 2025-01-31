import pytest
from unittest import mock

from api.cases.application_manifest import ManifestRegistry


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
