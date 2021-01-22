from django.conf import settings

from elasticsearch_dsl import Index

from api.applications import helpers, models
from test_helpers.clients import DataTestClient


class AutoMatchTests(DataTestClient):

    def test_auto_match_sanctions_no_matches(self):
        Index(settings.ELASTICSEARCH_SANCTION_INDEX_ALIAS).create(ignore=[400])
        import pdb; pdb.set_trace()
        application_data = self.create_standard_application_case(self.organisation)

        application = models.StandardApplication.objects.get(pk=application_data['pk'])
        helpers.auto_match_sanctions(application)

        self.assertEquals(application.sanction_matches.all().count(), 0)


    def test_auto_match_sanctions_match_name():
        pass


    def test_auto_match_sanctions_match_address():
        pass
