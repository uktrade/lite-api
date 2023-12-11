from test_helpers.clients import DataTestClient

from api.gov_users.serializers import GovUserViewSerializer
from api.queues.constants import ALL_CASES_QUEUE_ID, ALL_CASES_QUEUE_NAME
from api.queues.tests.factories import QueueFactory
from api.users.tests.factories import GovUserFactory


class GovUserViewSerializerTests(DataTestClient):
    def setUp(self):
        try:
            delattr(GovUserViewSerializer, "_queue_cache")
        except AttributeError:
            pass

    def test_default_queue_with_object_data(self):
        queue = QueueFactory()
        user = GovUserFactory(
            default_queue=str(queue.pk),
        )

        data = GovUserViewSerializer(user).data

        self.assertEqual(
            data["default_queue"],
            {"id": str(queue.pk), "name": queue.name},
        )

    def test_default_queue_with_system_queue(self):
        user = GovUserFactory(
            default_queue=ALL_CASES_QUEUE_ID,
        )

        data = GovUserViewSerializer(user).data

        self.assertEqual(
            data["default_queue"],
            {"id": ALL_CASES_QUEUE_ID, "name": ALL_CASES_QUEUE_NAME},
        )

    def test_caching_queue_lookup(self):
        queue = QueueFactory()
        user = GovUserFactory(
            default_queue=str(queue.pk),
        )

        with self.assertNumQueries(4):
            data = GovUserViewSerializer(user).data
            self.assertEqual(
                data["default_queue"],
                {"id": str(queue.pk), "name": queue.name},
            )

        # User role and queue are cached so we have 2 fewer queries run here
        # for this test we are explicitly only checking queue but that is why
        # we see two fewer queries as opposed to 1
        with self.assertNumQueries(2):
            data = GovUserViewSerializer(user).data
            self.assertEqual(
                data["default_queue"],
                {"id": str(queue.pk), "name": queue.name},
            )

    def test_caching_queue_lookup_new_queue(self):
        queue = QueueFactory()
        user = GovUserFactory(
            default_queue=str(queue.pk),
        )
        data = GovUserViewSerializer(user).data
        self.assertEqual(
            data["default_queue"],
            {"id": str(queue.pk), "name": queue.name},
        )

        new_queue = QueueFactory()
        new_user = GovUserFactory(
            default_queue=str(new_queue.pk),
        )
        data = GovUserViewSerializer(new_user).data
        self.assertEqual(
            data["default_queue"],
            {"id": str(new_queue.pk), "name": new_queue.name},
        )
