from parameterized import parameterized

from static.statuses.enums import CaseStatusEnum
from static.statuses.models import CaseStatus
from test_helpers.clients import DataTestClient
from workflow.user_queue_assignment import user_queue_assignment_workflow, get_next_non_terminal_status


class UserQueueAssignmentTests(DataTestClient):
    def setUp(self):
        super().setUp()
        self.case = self.create_standard_application_case(self.organisation)
        self.new_status = get_next_non_terminal_status(self.case.status)
        self.queue = self.create_queue("Abc", self.team)

    def test_no_queues_or_case_assignments(self):
        """
        As the case isn't assigned to any work queues, the case should move to the next status
        """
        user_queue_assignment_workflow([self.queue], self.case)

        self.case.refresh_from_db()
        self.assertEqual(self.case.status, self.new_status)

    def test_queue_but_no_case_assignments(self):
        """
        As no users are assigned to it, the case should be removed from the queue
        and the case should move to the next status
        """
        self.case.queues.add(self.queue)

        user_queue_assignment_workflow([self.queue], self.case)

        self.case.refresh_from_db()
        self.assertFalse(self.case.queues.exists())
        self.assertEqual(self.case.status, self.new_status)

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


class NextStatusTests(DataTestClient):
    def test_next_status_ignores_non_applicable_states(self):
        result = get_next_non_terminal_status(CaseStatus.objects.get(status=CaseStatusEnum.DRAFT))
        self.assertIsNone(result)

    @parameterized.expand(
        [
            [CaseStatusEnum.SUBMITTED, CaseStatusEnum.INITIAL_CHECKS],
            [CaseStatusEnum.RESUBMITTED, CaseStatusEnum.INITIAL_CHECKS],
            [CaseStatusEnum.INITIAL_CHECKS, CaseStatusEnum.UNDER_REVIEW],
            [CaseStatusEnum.UNDER_REVIEW, CaseStatusEnum.UNDER_FINAL_REVIEW],
            [CaseStatusEnum.REOPENED_FOR_CHANGES, CaseStatusEnum.CHANGE_INTIAL_REVIEW],
            [CaseStatusEnum.CHANGE_INTIAL_REVIEW, CaseStatusEnum.CHANGE_UNDER_REVIEW],
            [CaseStatusEnum.CHANGE_UNDER_REVIEW, CaseStatusEnum.CHANGE_UNDER_FINAL_REVIEW],
        ]
    )
    def test_next_status_increments(self, old_status, new_status):
        result = get_next_non_terminal_status(CaseStatus.objects.get(status=old_status))
        self.assertEqual(result.status, new_status)
