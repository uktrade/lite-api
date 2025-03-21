import pytest


@pytest.mark.django_db()
def test_populate_case_queue_movements(migrator):
    old_state = migrator.apply_initial_migration(("cases", "0084_alter_casetype_sub_type"))

    CaseType = old_state.apps.get_model("cases", "CaseType")
    with pytest.raises(CaseType.DoesNotExist):
        CaseType.objects.get(pk="00000000-0000-0000-0000-000000000017")

    migrator.apply_tested_migration(("cases", "0085_add_export_licence_case_type"))

    case_type = CaseType.objects.get(pk="00000000-0000-0000-0000-000000000017")
    assert case_type.type == "application"
    assert case_type.sub_type is None
    assert case_type.reference == "export_licence"
