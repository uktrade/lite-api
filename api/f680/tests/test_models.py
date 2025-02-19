import pytest

from .factories import F680ApplicationFactory


pytestmark = pytest.mark.django_db


@pytest.fixture
def data_application_json():
    return {
        "sections": {
            "general_application_details": {
                "fields": [
                    {
                        "key": "name",
                        "raw_answer": "some name",
                    }
                ]
            }
        }
    }


class TestF680Application:

    def test_on_submit_name_present_in_application_json(self, data_application_json):
        f680_application = F680ApplicationFactory(application=data_application_json)
        assert f680_application.name is None
        f680_application.on_submit()
        f680_application.refresh_from_db()
        assert f680_application.name == "some name"

    def test_on_submit_name_missing_in_application_json(self):
        f680_application = F680ApplicationFactory()
        assert f680_application.name is None
        f680_application.on_submit()
        f680_application.refresh_from_db()
        assert f680_application.name is None

    def test_get_application_field_value_field_present(self, data_application_json):
        f680_application = F680ApplicationFactory(application=data_application_json)
        assert f680_application.get_application_field_value("general_application_details", "name") == "some name"

    def test_get_application_field_value_field_missing(self, data_application_json):
        f680_application = F680ApplicationFactory(application=data_application_json)
        assert f680_application.get_application_field_value("general_application_details", "foo") is None

    def test_get_application_field_value_section_missing(self, data_application_json):
        f680_application = F680ApplicationFactory(application=data_application_json)
        assert f680_application.get_application_field_value("bar", "name") is None
