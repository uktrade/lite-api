import pytest

from api.application_manifests.registry import ManifestRegistry


def test_register(mocker):
    registry = ManifestRegistry()

    MockManifest = mocker.Mock()
    _register = registry.register("some_application_type")
    _register(MockManifest)

    assert registry.get_manifest("some_application_type") == MockManifest()


def test_register_with_decorator():
    registry = ManifestRegistry()

    @registry.register("some_application_type")
    class MockManifest:
        pass

    assert isinstance(registry.get_manifest("some_application_type"), MockManifest)


def test_register_missing_application_type():
    registry = ManifestRegistry()
    with pytest.raises(KeyError):
        registry.get_manifest("some_application_type")
