from unittest.mock import call, patch

from api.search.tasks import update_search_index
from test_helpers.clients import DataTestClient


class UpdateSearchIndexTests(DataTestClient):
    @patch("api.search.tasks.registry")
    def test_update_index(self, mock_registry):
        app1 = self.create_standard_application_case(self.organisation)
        app2 = self.create_standard_application_case(self.organisation)

        update_search_index.now("applications.StandardApplication", str(app1.pk), str(app2.pk))

        mock_registry.update.assert_has_calls([call(app1), call(app2)])
