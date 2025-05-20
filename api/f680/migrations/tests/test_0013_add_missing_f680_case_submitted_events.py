from api.audit_trail.enums import AuditType
from api.f680.tests.factories import F680ApplicationFactory, SubmittedF680ApplicationFactory
from api.staticdata.statuses.enums import CaseStatusEnum
from api.users.enums import SystemUser
import pytest


INITIAL_MIGRATION = "0012_recommendation_security_grading_and_more"
MIGRATION_UNDER_TEST = "0013_add_missing_f680_case_submitted_events"


@pytest.mark.django_db()
def test_add_missing_f680_case_submitted_events(migrator):
    old_state = migrator.apply_initial_migration(("f680", INITIAL_MIGRATION))

    app_1 = F680ApplicationFactory()
    app_2 = SubmittedF680ApplicationFactory()
    app_3 = SubmittedF680ApplicationFactory()
    BaseUser = old_state.apps.get_model("users", "BaseUser")
    BaseUser.objects.create(id=SystemUser.id, email="fake@email.com")

    new_state = migrator.apply_tested_migration(("f680", MIGRATION_UNDER_TEST))

    ContentType = new_state.apps.get_model("contenttypes", "ContentType")

    case_content_type = ContentType.objects.get(model="case")
    baseuser_content_type = ContentType.objects.get(model="baseuser")

    Audit = new_state.apps.get_model("audit_trail", "Audit")
    F680Application = new_state.apps.get_model("f680", "F680Application")

    F680Applications = F680Application.objects.exclude(status__status=CaseStatusEnum.DRAFT)

    assert F680Applications.count() == 2
    assert Audit.objects.all().count() == 2

    for f680_application in F680Applications:
        audit = Audit.objects.get(target_object_id=f680_application.pk)
        assert audit.created_at == f680_application.submitted_at
        assert audit.updated_at == f680_application.submitted_at
        assert audit.actor_object_id == f680_application.submitted_by.pk
        assert audit.actor_content_type == baseuser_content_type
        assert audit.actor_content_type_id == baseuser_content_type.id
        assert audit.target_content_type_id == case_content_type.id
        assert audit.target_content_type == case_content_type
        assert audit.verb == AuditType.UPDATED_STATUS
        assert audit.payload == {
            "status": {"new": CaseStatusEnum.SUBMITTED, "old": CaseStatusEnum.DRAFT},
            "additional_text": "",
        }
