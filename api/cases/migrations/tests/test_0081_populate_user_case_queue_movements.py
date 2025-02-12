import pytest

from api.cases.tests.factories import CaseFactory
from api.queues.tests.factories import QueueFactory
from api.users.tests.factories import SystemUserFactory


@pytest.mark.django_db()
def test_populate_user_case_queue_movements(migrator):
    old_state = migrator.apply_initial_migration(("cases", "0080_casequeuemovement_user"))

    CaseQueueMovement = old_state.apps.get_model("cases", "CaseQueueMovement")

    system_user = SystemUserFactory()

    for _ in range(25):
        case = CaseFactory()
        queue = QueueFactory()
        CaseQueueMovement.objects.create(case_id=case.id, queue_id=queue.id, user=None)

    migrator.apply_tested_migration(("cases", "0081_populate_user_case_queue_movements"))

    assert set(CaseQueueMovement.objects.all().values_list("user_id", flat=True)) == {system_user.id}
