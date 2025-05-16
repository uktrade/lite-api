import pytest
from django_test_migrations.contrib.unittest_case import MigratorTestCase


@pytest.mark.django_db()
class TestSurveyResponseMigration(MigratorTestCase):
    migrate_from = ("survey", "0001_initial")
    migrate_to = ("survey", "0002_surveyresponse_case_type")

    def test_surveyresponse_data_updates(self):
        SurveyResponse = self.new_state.apps.get_model("survey", "SurveyResponse")

        assert SurveyResponse.objects.filter(case_type__isnull=True).count() == 0
