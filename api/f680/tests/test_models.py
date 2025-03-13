import pytest

from .factories import F680ApplicationFactory

from api.f680.models import Product, SecurityReleaseRequest


pytestmark = pytest.mark.django_db


class TestF680Application:

    def test_on_submit_fields_present_in_application_json(
        self, data_application_json, data_australia_release_id, data_france_release_id, data_uae_release_id
    ):
        f680_application = F680ApplicationFactory(application=data_application_json)
        assert f680_application.name is None
        f680_application.on_submit()
        f680_application.refresh_from_db()
        assert f680_application.name == "some name"

        assert Product.objects.all().count() == 1
        product = Product.objects.first()
        assert product.name == "some product name"
        assert product.description == "some product description"
        assert product.security_grading == "official"
        assert product.organisation == f680_application.organisation

        expected_security_release_count = len(data_application_json["sections"]["user_information"]["items"])
        assert f680_application.security_release_requests.all().count() == expected_security_release_count

        australia_release = SecurityReleaseRequest.objects.get(id=data_australia_release_id)
        australia_recipient = australia_release.recipient
        assert australia_recipient.name == "australia name"
        assert australia_recipient.address == "australia address"
        assert australia_recipient.country_id == "AU"
        assert australia_recipient.type == "third-party"
        assert australia_recipient.organisation == f680_application.organisation
        assert australia_recipient.role == "consultant"
        assert australia_release.product == product
        assert australia_release.security_grading == "secret"
        assert australia_release.intended_use == "australia intended use"

        france_release = SecurityReleaseRequest.objects.get(id=data_france_release_id)
        france_recipient = france_release.recipient
        assert france_recipient.name == "france name"
        assert france_recipient.address == "france address"
        assert france_recipient.country_id == "FR"
        assert france_recipient.type == "ultimate-end-user"
        assert france_recipient.organisation == f680_application.organisation
        assert france_release.product == product
        assert france_release.security_grading == "official"
        assert france_release.intended_use == "france intended use"

        uae_release = SecurityReleaseRequest.objects.get(id=data_uae_release_id)
        uae_recipient = uae_release.recipient
        assert uae_recipient.name == "uae name"
        assert uae_recipient.address == "uae address"
        assert uae_recipient.country_id == "AE"
        assert uae_recipient.type == "end-user"
        assert uae_recipient.organisation == f680_application.organisation
        assert uae_release.product == product
        assert uae_release.security_grading == "top-secret"
        assert uae_release.intended_use == "uae intended use"

    def test_on_submit_name_missing_in_application_json(self):
        f680_application = F680ApplicationFactory()
        assert f680_application.name is None
        with pytest.raises(KeyError):
            f680_application.on_submit()

    def test_get_application_field_value_field_present(self, data_application_json):
        f680_application = F680ApplicationFactory(application=data_application_json)
        assert f680_application.get_application_field_value("general_application_details", "name") == "some name"

    def test_get_application_field_value_field_missing_exception_raised(self, data_application_json):
        f680_application = F680ApplicationFactory(application=data_application_json)
        with pytest.raises(KeyError):
            f680_application.get_application_field_value("general_application_details", "foo")

    def test_get_application_field_value_section_missing(self, data_application_json):
        f680_application = F680ApplicationFactory(application=data_application_json)
        with pytest.raises(KeyError):
            f680_application.get_application_field_value("bar", "name")

    def test_get_field_value_field_exists(self):
        f680_application = F680ApplicationFactory()
        fields = [{"key": "foo", "raw_answer": "bar"}, {"key": "a", "raw_answer": "b"}]
        assert f680_application.get_field_value(fields, "a") == "b"

    def test_get_field_value_field_missing_exception_raised(self):
        f680_application = F680ApplicationFactory()
        fields = [{"key": "foo", "raw_answer": "bar"}, {"key": "a", "raw_answer": "b"}]
        with pytest.raises(KeyError):
            f680_application.get_field_value(fields, "missing")

    def test_get_field_value_field_missing_no_exception(self):
        f680_application = F680ApplicationFactory()
        fields = [{"key": "foo", "raw_answer": "bar"}, {"key": "a", "raw_answer": "b"}]
        assert f680_application.get_field_value(fields, "missing", raise_exception=False) == None
