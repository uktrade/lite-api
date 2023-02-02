from api.audit_trail.enums import AuditType
from api.audit_trail.models import Audit
from api.cases.models import Case
from api.cases.views.search import service
from django.contrib.contenttypes.models import ContentType
from test_helpers.clients import DataTestClient


class TestSearchService(DataTestClient):
    def setUp(self):
        super().setUp()

    def test_populate_activity_updates(self):
        self.case = self.create_standard_application_case(self.organisation).get_case()
        new_status = "1"
        Audit.objects.create(
            actor=self.gov_user,
            verb=AuditType.UPDATED_STATUS,
            action_object_object_id=self.case.id,
            action_object_content_type=ContentType.objects.get_for_model(Case),
            payload={"status": {"new": new_status, "old": "2"}},
        )
        old_name = "old_app_name"
        new_name = "new_app_name"
        Audit.objects.create(
            actor=self.exporter_user,
            verb=AuditType.UPDATED_APPLICATION_NAME,
            target_object_id=self.case.id,
            target_content_type=ContentType.objects.get_for_model(Case),
            payload={"old_name": old_name, "new_name": new_name},
        )
        cases = service.populate_activity_updates([{"id": str(self.case.id)}])
        # check only 2 records are present, sorted newest first
        assert len(cases[0]["activity_updates"]) == 2
        assert (
            cases[0]["activity_updates"][0]["text"]
            == f'updated the application name from "{old_name}" to "{new_name}".'
        )
        assert cases[0]["activity_updates"][1]["text"] == f"updated the status to: {new_status}."
