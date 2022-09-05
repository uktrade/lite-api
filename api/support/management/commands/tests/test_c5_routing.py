from unittest import mock

from django.core.management import call_command

from test_helpers.clients import DataTestClient


class C5RoutingMgmtCommandTests(DataTestClient):
    @mock.patch("lite_routing.routing_rules_internal.tests.helpers.activate_c5_routing")
    def test_activating_rules(self, mock_activate_c5_routing):
        call_command("c5_routing", "activate")
        assert mock_activate_c5_routing.called

    @mock.patch("lite_routing.routing_rules_internal.tests.helpers.deactivate_c5_routing")
    def test_deactivating_rules(self, mock_deactivate_c5_routing):
        call_command("c5_routing", "deactivate")
        assert mock_deactivate_c5_routing.called
