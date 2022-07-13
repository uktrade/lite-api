from django.conf import settings

from test_helpers.clients import DataTestClient
from parameterized import parameterized
from api.staticdata.control_list_entries.models import ControlListEntry


gona_copy_logger = settings.GOOD_ON_APPLICATION_COPY_LOGGER


class GoodOnApplicationSave(DataTestClient):
    @parameterized.expand(
        [
            [
                ["ML1a"],
                ["ML1a"],
            ],
            [
                ["ML1a", "ML1b"],
                ["ML1a", "ML1b"],
            ],
        ]
    )
    def test_save_log(self, good_cle, gona_cle):
        with self.assertLogs(logger=gona_copy_logger, level="WARNING") as log:
            application = self.create_draft_standard_application(
                organisation=self.organisation, user=self.exporter_user
            )
            good = self.create_good(
                "A good", self.organisation, is_good_controlled=good_cle != [], control_list_entries=good_cle
            )
            gona = self.create_good_on_application(application, good)
            gona.control_list_entries.set(ControlListEntry.objects.filter(rating__in=gona_cle))
            gona.save()
            assert len(log.output) == 1
            exp_log = f"WARNING:good_on_application_copy_logger:Saving GoodOnApplication ({str(gona.id)}) with CLE copied from Good: ({str(good.id)})"
            assert exp_log in log.output[0]

    @parameterized.expand(
        [
            [
                [],
                [],
            ],
            [
                ["ML1a"],
                [],
            ],
            [
                [],
                ["ML1a"],
            ],
            [
                ["ML1a", "ML1b"],
                ["ML1a"],
            ],
        ]
    )
    def test_save_no_log(self, good_cle, gona_cle):
        with self.assertRaises(AssertionError) as err, self.assertLogs(logger=gona_copy_logger, level="WARNING"):
            application = self.create_draft_standard_application(
                organisation=self.organisation, user=self.exporter_user
            )
            good = self.create_good(
                "A good", self.organisation, is_good_controlled=good_cle != [], control_list_entries=good_cle
            )
            gona = self.create_good_on_application(application, good)
            gona.control_list_entries.set(ControlListEntry.objects.filter(rating__in=gona_cle))
            gona.save()
        self.assertEqual(f"no logs of level WARNING or higher triggered on {gona_copy_logger}", str(err.exception))
