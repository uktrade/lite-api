# api/application_manifests/tests/test_settings.py
import pytest
from django.urls import reverse
from rest_framework import status

from api.application_manifests.models import ApplicationManifestFeatures
from api.application_manifests.tests.test_features import authorized_client
from api.cases.enums import ApplicationFeatures, CaseTypeReferenceEnum


@pytest.mark.django_db
class TestApplicationManifestSettings:

    @pytest.fixture
    def manifest_features(self):
        return ApplicationManifestFeatures.objects.create(
            case_type=CaseTypeReferenceEnum.F680,
            features={
                ApplicationFeatures.LICENCE_ISSUE.value: True,
                ApplicationFeatures.ROUTE_TO_COUNTERSIGNING_QUEUES.value: False,
            },
        )

    @pytest.fixture
    def url(self):
        return reverse("application-manifest:manifest-feature-list")

    @pytest.fixture
    def detail_url(self, manifest_features):
        return reverse(
            "application-manifest:manifest-feature-detail", kwargs={"case_type": manifest_features.case_type}
        )

    def test_create_settings(self, authorized_client, url):
        data = {
            "case_type": CaseTypeReferenceEnum.F680,
            "features": {
                ApplicationFeatures.LICENCE_ISSUE.value: True,
                ApplicationFeatures.ROUTE_TO_COUNTERSIGNING_QUEUES.value: False,
            },
        }

        response = authorized_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert ApplicationManifestFeatures.objects.count() == 1
        assert response.data["features"] == data["features"]

    def test_create_settings_invalid_feature(self, authorized_client, url):
        data = {
            "case_type": CaseTypeReferenceEnum.F680,
            "features": {"INVALID_FEATURE": True},
        }

        response = authorized_client.post(url, data, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Invalid Features: INVALID_FEATURE" in str(response.data)

    def test_get_settings(self, authorized_client, url, manifest_features):
        response = authorized_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["case_type"] == manifest_features.case_type

    def test_update_settings(self, authorized_client, detail_url, manifest_features):
        data = {
            "features": {
                ApplicationFeatures.LICENCE_ISSUE.value: False,
                ApplicationFeatures.ROUTE_TO_COUNTERSIGNING_QUEUES.value: True,
            }
        }

        response = authorized_client.patch(detail_url, data, format="json")
        assert response.status_code == status.HTTP_200_OK
        manifest_features.refresh_from_db()
        assert manifest_features.features == data["features"]

    def test_update_single_feature(self, authorized_client, detail_url, manifest_features):
        url = f"{detail_url}update_feature/"
        data = {
            "feature_name": ApplicationFeatures.LICENCE_ISSUE.value,
            "feature_value": False,
        }

        response = authorized_client.patch(url, data, format="json")
        assert response.status_code == status.HTTP_200_OK
        manifest_features.refresh_from_db()
        assert manifest_features.features[ApplicationFeatures.LICENCE_ISSUE.value] is False

    @pytest.mark.django_db(transaction=True)
    def test_features_cache(self, manifest_features):
        from api.application_manifests.base import BaseManifest

        class TestManifest(BaseManifest):
            def __init__(self):
                super().__init__()
                self.case_type_reference = CaseTypeReferenceEnum.F680
                self.features = {
                    ApplicationFeatures.LICENCE_ISSUE.value: True,
                    ApplicationFeatures.ROUTE_TO_COUNTERSIGNING_QUEUES.value: True,
                }

        manifest = TestManifest()
        manifest.features[ApplicationFeatures.LICENCE_ISSUE.value] = False
        assert manifest.has_feature(ApplicationFeatures.LICENCE_ISSUE.value) is False
        manifest.features = None
        assert manifest.has_feature(ApplicationFeatures.LICENCE_ISSUE.value) is False
