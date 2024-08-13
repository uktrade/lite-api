import pytest
from django_test_migrations.migrator import Migrator


statuses_to_remove = ["revoked", "suspended"]
statuses_to_remove_create = ["revoked", "suspended", "draft"]
user_permissions = ["Licensing Unit Manager", "Licencing Unit Senior Manager", "Super User"]


def prepare(old_state):

    UserRoleStatus = old_state.apps.get_model("users", "role_statuses")
    CaseStatus = old_state.apps.get_model("statuses", "casestatus")
    Role = old_state.apps.get_model("users", "role")

    for status in statuses_to_remove_create:
        StatusObject, _ = CaseStatus.objects.get_or_create(status=status)
        for permission in user_permissions:
            RoleObject, _ = Role.objects.get_or_create(name=permission, type="internal")
            UserRoleStatus.objects.get_or_create(role_id=RoleObject.id, casestatus_id=StatusObject.id)


@pytest.mark.django_db()
def test_remove_user_role_status():
    migrator = Migrator(database="default")
    old_state = migrator.apply_initial_migration(("users", "0006_alter_userorganisationrelationship_user"))
    prepare(old_state)

    UserRoleStatusOld = old_state.apps.get_model("users", "role_statuses")
    assert UserRoleStatusOld.objects.filter(casestatus__status__in=statuses_to_remove_create).count() == 9

    new_state = migrator.apply_tested_migration(("users", "0007_remove_user_role_status_permissions"))

    UserRoleStatusNew = new_state.apps.get_model("users", "role_statuses")

    assert UserRoleStatusNew.objects.filter(casestatus__status__in=statuses_to_remove_create).count() == 3
