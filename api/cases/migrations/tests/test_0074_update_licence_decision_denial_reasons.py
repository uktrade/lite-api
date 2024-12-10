import pytest

from api.applications.tests.factories import StandardApplicationFactory
from api.audit_trail.enums import AuditType
from api.audit_trail.tests.factories import AuditFactory
from api.cases.enums import (
    AdviceType,
    LicenceDecisionType,
)
from api.cases.tests.factories import (
    FinalAdviceFactory,
    LicenceDecisionFactory,
    TeamAdviceFactory,
    UserAdviceFactory,
)
from api.users.tests.factories import (
    GovUserFactory,
    RoleFactory,
)


@pytest.mark.django_db()
def test_attach_licence_to_licence_decisions(migrator):
    migrator.apply_initial_migration(("cases", "0073_licencedecision_denial_reasons"))

    LICENSING_UNIT_ID = "58e77e47-42c8-499f-a58d-94f94541f8c6"
    FCDO_ID = "67b9a4a3-6f3d-4511-8a19-23ccff221a74"

    RoleFactory(id="00000000-0000-0000-0000-000000000001")
    lu_user = GovUserFactory(team_id=LICENSING_UNIT_ID)
    fcdo_user = GovUserFactory(team_id=FCDO_ID)

    refused_application = StandardApplicationFactory()
    refused_licence_decision = LicenceDecisionFactory(
        case=refused_application,
        decision=LicenceDecisionType.REFUSED,
    )
    UserAdviceFactory(
        case=refused_application,
        denial_reasons=["1"],
        team_id=FCDO_ID,
        type=AdviceType.REFUSE,
        user=fcdo_user,
    )
    UserAdviceFactory(
        case=refused_application,
        denial_reasons=["2"],
        team_id=LICENSING_UNIT_ID,
        type=AdviceType.REFUSE,
        user=lu_user,
    )
    TeamAdviceFactory(
        case=refused_application,
        denial_reasons=["3"],
        team_id=FCDO_ID,
        type=AdviceType.REFUSE,
        user=fcdo_user,
    )
    TeamAdviceFactory(
        case=refused_application,
        denial_reasons=["4"],
        team_id=LICENSING_UNIT_ID,
        type=AdviceType.REFUSE,
        user=lu_user,
    )
    FinalAdviceFactory(
        case=refused_application,
        denial_reasons=["5"],
        team_id=LICENSING_UNIT_ID,
        type=AdviceType.REFUSE,
        user=lu_user,
    )
    assert list(refused_licence_decision.denial_reasons.values_list("id", flat=True)) == []

    migrator.apply_tested_migration(("cases", "0074_update_licence_decision_denial_reasons"))
    refused_licence_decision.refresh_from_db()
    assert list(refused_licence_decision.denial_reasons.values_list("id", flat=True)) == ["5"]


@pytest.mark.django_db()
def test_attach_licence_to_licence_decisions_without_denial_reasons_on_advice(migrator):
    old_state = migrator.apply_initial_migration(("cases", "0073_licencedecision_denial_reasons"))

    refused_application = StandardApplicationFactory()
    refused_licence_decision = LicenceDecisionFactory(
        case=refused_application,
        decision=LicenceDecisionType.REFUSED,
    )
    assert list(refused_licence_decision.denial_reasons.values_list("id", flat=True)) == []
    assert not refused_application.advice.exists()

    Case = old_state.apps.get_model("cases", "Case")
    ContentType = old_state.apps.get_model("contenttypes", "ContentType")
    case_content_type = ContentType.objects.get_for_model(Case)

    AuditFactory(
        payload={
            "additional_text": "1, 5, 7.",
        },
        target_content_type_id=case_content_type.pk,
        target_object_id=refused_application.pk,
        verb=AuditType.CREATE_REFUSAL_CRITERIA,
    )

    migrator.apply_tested_migration(("cases", "0074_update_licence_decision_denial_reasons"))
    refused_licence_decision.refresh_from_db()
    assert list(refused_licence_decision.denial_reasons.values_list("id", flat=True)) == ["1", "5", "7"]
