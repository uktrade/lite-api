from api.audit_trail.enums import AuditType
from api.audit_trail.models import Audit
from api.cases.models import Case
from api.cases.views.search import service
from django.contrib.contenttypes.models import ContentType
from lite_routing.routing_rules_internal.enums import FlagsEnum
from test_helpers.clients import DataTestClient


class TestSearchService(DataTestClient):
    def setUp(self):
        super().setUp()

    def test_populate_activity_updates(self):
        self.case = self.create_standard_application_case(self.organisation).get_case()
        new_status = "1"
        Audit.objects.create(
            actor=self.exporter_user,
            verb=AuditType.UPDATED_APPLICATION_NAME,
            target_object_id=self.case.id,
            target_content_type=ContentType.objects.get_for_model(Case),
            payload={"old_name": "draft", "new_name": "2nd_draft"},
        )
        Audit.objects.create(
            actor=self.exporter_user,
            verb=AuditType.UPDATED_APPLICATION_NAME,
            target_object_id=self.case.id,
            target_content_type=ContentType.objects.get_for_model(Case),
            payload={"old_name": "2nd_draft", "new_name": "3rd_draft"},
        )
        Audit.objects.create(
            actor=self.system_user,
            verb=AuditType.ADDED_FLAG_ON_ORGANISATION,
            target_object_id=self.case.id,
            target_content_type=ContentType.objects.get_for_model(Case),
            payload={"flag_name": FlagsEnum.AG_CHEMICAL, "additional_text": "additional note here"},
        )
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
        case_id = str(self.case.id)
        case_map = {case_id: {"id": case_id}}
        service.populate_activity_updates(case_map)
        # check only 2 records are present, sorted newest first
        assert len(case_map[case_id]["activity_updates"]) == 2
        assert (
            case_map[case_id]["activity_updates"][0]["text"]
            == f'updated the application name from "{old_name}" to "{new_name}".'
        )
        assert case_map[case_id]["activity_updates"][1]["text"] == f"updated the status to: {new_status}."
