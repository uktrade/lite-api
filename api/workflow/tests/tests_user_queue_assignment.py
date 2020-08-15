from parameterized import parameterized

from api.queues.tests.factories import QueueFactory
from api.static.statuses.enums import CaseStatusEnum
from api.static.statuses.models import CaseStatus
from test_helpers.clients import DataTestClient
from api.workflow.user_queue_assignment import user_queue_assignment_workflow, get_next_status_in_workflow_sequence


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
        self.assertFalse(self.case.queues.exists())
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


class NextStatusTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.case = self.create_standard_application_case(self.organisation)

    def test_next_status_ignores_non_applicable_states(self):
        self.case.status = CaseStatus.objects.get(status=CaseStatusEnum.DRAFT)
        self.case.save()
        result = get_next_status_in_workflow_sequence(self.case)
        self.assertIsNone(result)

    @parameterized.expand(
        [
            [CaseStatusEnum.SUBMITTED, CaseStatusEnum.INITIAL_CHECKS],
            [CaseStatusEnum.RESUBMITTED, CaseStatusEnum.INITIAL_CHECKS],
            [CaseStatusEnum.INITIAL_CHECKS, CaseStatusEnum.UNDER_REVIEW],
            [CaseStatusEnum.UNDER_REVIEW, CaseStatusEnum.OGD_ADVICE],
            [CaseStatusEnum.OGD_ADVICE, CaseStatusEnum.UNDER_FINAL_REVIEW],
            [CaseStatusEnum.REOPENED_FOR_CHANGES, CaseStatusEnum.CHANGE_INTIAL_REVIEW],
            [CaseStatusEnum.CHANGE_INTIAL_REVIEW, CaseStatusEnum.CHANGE_UNDER_REVIEW],
            [CaseStatusEnum.CHANGE_UNDER_REVIEW, CaseStatusEnum.CHANGE_UNDER_FINAL_REVIEW],
        ]
    )
    def test_next_status_increments(self, old_status, new_status):
        self.case.status = CaseStatus.objects.get(status=old_status)
        self.case.save()
        result = get_next_status_in_workflow_sequence(self.case)
        self.assertEqual(result.status, new_status)


class NextStatusGoodsQueryTests(DataTestClient):
    def test_next_status_ignores_submitted(self):
        case = self.create_goods_query("abc", self.organisation, "clc", "pv")
        result = get_next_status_in_workflow_sequence(case)
        self.assertIsNone(result)

    def test_next_status_moves_to_pv_if_clc_responded(self):
        case = self.create_goods_query("abc", self.organisation, "clc", "pv")
        case.clc_responded = True
        case.save()
        result = get_next_status_in_workflow_sequence(case)
        self.assertEqual(result.status, CaseStatusEnum.PV)

    def test_next_status_moves_to_pv_if_no_clc(self):
        case = self.create_goods_query("abc", self.organisation, None, "pv")
        result = get_next_status_in_workflow_sequence(case)
        self.assertEqual(result.status, CaseStatusEnum.PV)

    def test_statues_doesnt_move_if_clc_not_responded(self):
        case = self.create_goods_query("abc", self.organisation, "clc", "pv")
        result = get_next_status_in_workflow_sequence(case)
        self.assertIsNone(result)

    def test_status_doesnt_move_if_no_pv_responded(self):
        case = self.create_goods_query("abc", self.organisation, "clc", None)
        case.clc_responded = True
        case.save()
        result = get_next_status_in_workflow_sequence(case)
        self.assertIsNone(result)
