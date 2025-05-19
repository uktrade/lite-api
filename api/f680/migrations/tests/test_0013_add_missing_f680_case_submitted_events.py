from api.audit_trail.enums import AuditType
from api.f680.tests.factories import F680ApplicationFactory
from api.staticdata.statuses.enums import CaseStatusEnum
from api.users.enums import SystemUser
import pytest


INITIAL_MIGRATION = "0012_recommendation_security_grading_and_more"
MIGRATION_UNDER_TEST = "0013_add_missing_f680_case_submitted_events"


@pytest.mark.django_db()
def test_add_missing_f680_case_submitted_events(migrator):
    old_state = migrator.apply_initial_migration(("f680", INITIAL_MIGRATION))
    app_1 = F680ApplicationFactory()
    app_2 = F680ApplicationFactory()

    new_state = migrator.apply_tested_migration(("f680", MIGRATION_UNDER_TEST))

    Audit = new_state.apps.get_model("audit_trail", "Audit")
    F680Application = new_state.apps.get_model("f680", "F680Application")

    audits = Audit.objects.all()

    F680Applications = F680Application.objects.all()
    assert F680Applications.count() == 2
    assert Audit.objects.all().count() == 2
    for f680_application in F680Applications:
        audit = Audit.objects.get(target_object_id=f680_application.id)
        assert audit.created_at == f680_application.created_at
        assert audit.updated_at == f680_application.updated_at
        assert audit.actor_object_id == SystemUser.id
        assert audit.verb == AuditType.UPDATED_STATUS
        assert audit.payload == {
            "status": {"new": CaseStatusEnum.SUBMITTED, "old": CaseStatusEnum.DRAFT},
            "additional_text": "",
        }
