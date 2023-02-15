from parameterized import parameterized

from api.queues.tests.factories import QueueFactory
from test_helpers.clients import DataTestClient
from api.workflow.user_queue_assignment import user_queue_assignment_workflow

from lite_routing.routing_rules_internal.routing_engine import get_next_status_in_workflow_sequence


class UserQueueAssignmentTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.case = self.create_standard_application_case(self.organisation)
        self.new_status = get_next_status_in_workflow_sequence(self.case)
        self.queue = self.create_queue("Abc", self.team)

    def test_no_queues_or_case_assignments(self):
        """
        As the case isn't assigned to any work queues, the case should move to the next status
        """
        old_status = self.case.status
        user_queue_assignment_workflow([self.queue], self.case)

        self.case.refresh_from_db()
        self.assertGreater(self.case.status.priority, old_status.priority)

    def test_queue_but_no_case_assignments(self):
        """
        As no users are assigned to it, the case should be removed from the queue
        and the case should move to the next status
        """
        old_status = self.case.status
        self.case.queues.add(self.queue)

        user_queue_assignment_workflow([self.queue], self.case)

        self.case.refresh_from_db()
        self.assertTrue(self.case.queues.exists())
        self.assertGreater(self.case.status.priority, old_status.priority)

    def test_queue_and_case_assignment(self):
        """
        As users are still assigned to this case on the queue,
        the queue shouldn't be removed and the status shouldn't change
        """
        self.create_case_assignment(self.queue, self.case, [self.gov_user])
        self.case.queues.add(self.queue)

        user_queue_assignment_workflow([self.queue], self.case)

        self.case.refresh_from_db()
        self.assertTrue(self.case.queues.exists())
        self.assertNotEqual(self.case.status, self.new_status)

    def test_multiple_queues_and_case_assignment(self):
        """
        Queue's without any assigned users should be removed, but
        as a there is still a case assignment on a queue, that queue should
        remain and the status shouldn't change
        """
        other_queue = self.create_queue("Other", self.team)
        self.create_case_assignment(self.queue, self.case, [self.gov_user])
        self.case.queues.set([self.queue, other_queue])

        user_queue_assignment_workflow([self.queue, other_queue], self.case)

        self.case.refresh_from_db()
        self.assertEqual(self.case.queues.count(), 1)
        self.assertEqual(self.case.queues.first(), self.queue)
        self.assertNotEqual(self.case.status, self.new_status)

    def test_multiple_case_assignments(self):
        """
        As multiple users are on the queue, when you remove yourself from the queue
        the case should remain assigned to the queue and the status shouldn't change
        """
        other_user = self.create_gov_user("other@gmail.com", self.team)
        self.create_case_assignment(self.queue, self.case, [self.gov_user, other_user])
        self.case.queues.add(self.queue)

        user_queue_assignment_workflow([self.queue], self.case)

        self.case.refresh_from_db()
        self.assertEqual(self.case.queues.count(), 1)
        self.assertEqual(self.case.queues.first(), self.queue)
        self.assertNotEqual(self.case.status, self.new_status)

    def test_countersigning_queue(self):
        """
        Tests that countersigning queues are assigned when work queue removed, and status is not change
        """
        old_status = self.case.status
        countersigning_queue = QueueFactory(name="other", team=self.team)
        self.queue.countersigning_queue = countersigning_queue
        self.queue.save()
        user_queue_assignment_workflow([self.queue], self.case)

        self.case.refresh_from_db()
        self.assertIn(countersigning_queue, self.case.queues.all())
        self.assertNotIn(self.queue, self.case.queues.all())
        self.assertEqual(self.case.status, old_status)

    def test_countersigning_queue_multiple_feeder_queues(self):
        """
        Tests that countersigning queues are assigned when last "feeder" work queue removed, and status is not changed
        """
        old_status = self.case.status
        countersigning_queue = QueueFactory(name="other", team=self.team)
        feeder_queue_1 = QueueFactory(name="feeder 1", team=self.team, countersigning_queue=countersigning_queue)
        feeder_queue_2 = QueueFactory(name="feeder 2", team=self.team, countersigning_queue=countersigning_queue)
        self.case.queues.set([feeder_queue_1, feeder_queue_2])

        user_queue_assignment_workflow([feeder_queue_1], self.case)

        self.case.refresh_from_db()
        self.assertNotIn(countersigning_queue, self.case.queues.all())
        self.assertNotIn(feeder_queue_1, self.case.queues.all())
        self.assertEqual(self.case.status, old_status)

        user_queue_assignment_workflow([feeder_queue_2], self.case)

        self.case.refresh_from_db()
        self.assertIn(countersigning_queue, self.case.queues.all())
        self.assertNotIn(feeder_queue_2, self.case.queues.all())
        self.assertEqual(self.case.status, old_status)
