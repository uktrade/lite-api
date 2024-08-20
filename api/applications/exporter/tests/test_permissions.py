from unittest import mock
from parameterized import parameterized

from api.applications.exporter.permissions import CaseStatusExporterChangeable
from api.applications.tests.factories import StandardApplicationFactory
from api.staticdata.statuses.enums import CaseStatusEnum
from api.staticdata.statuses.models import CaseStatus


from test_helpers.clients import DataTestClient

non_terminal_statuses = list(set(CaseStatusEnum.all()) - set(CaseStatusEnum.terminal_statuses()))
non_finalised_statuses = list(set(CaseStatusEnum.all()) - set([CaseStatusEnum.FINALISED]))
non_major_editable_statuses = list(set(CaseStatusEnum.all()) - set(CaseStatusEnum.can_invoke_major_edit_statuses()))
non_exporter_eligible_statuses = list(
    set(CaseStatusEnum.all())
    - set([CaseStatusEnum.WITHDRAWN, CaseStatusEnum.SURRENDERED, CaseStatusEnum.APPLICANT_EDITING])
)


class TestChangeStatusExporterChangeable(DataTestClient):

    def setUp(self):
        super().setUp()
        self.application = StandardApplicationFactory(status=CaseStatus.objects.get(status=CaseStatusEnum.SUBMITTED))
        self.permission_obj = CaseStatusExporterChangeable()

    @parameterized.expand(non_terminal_statuses)
    def test_has_object_permission_set_withdrawn_permitted(self, original_status):
        self.application.status = CaseStatus.objects.get(status=original_status)
        self.application.save()

        mock_request = mock.Mock()
        mock_request.data = {"status": CaseStatusEnum.WITHDRAWN}
        mock_request.user = self.exporter_user.baseuser_ptr
        assert self.permission_obj.has_object_permission(mock_request, None, self.application) is True

    @parameterized.expand(CaseStatusEnum.terminal_statuses())
    def test_has_object_permission_set_withdrawn_not_permitted(self, original_status):
        self.application.status = CaseStatus.objects.get(status=original_status)
        self.application.save()

        mock_request = mock.Mock()
        mock_request.data = {"status": CaseStatusEnum.WITHDRAWN}
        mock_request.user = self.exporter_user.baseuser_ptr
        assert self.permission_obj.has_object_permission(mock_request, None, self.application) is False

    def test_has_object_permission_set_surrendered_permitted(self):
        self.application.status = CaseStatus.objects.get(status=CaseStatusEnum.FINALISED)
        self.application.save()

        mock_request = mock.Mock()
        mock_request.data = {"status": CaseStatusEnum.SURRENDERED}
        mock_request.user = self.exporter_user.baseuser_ptr
        assert self.permission_obj.has_object_permission(mock_request, None, self.application) is True

    @parameterized.expand(non_finalised_statuses)
    def test_has_object_permission_set_surrendered_not_permitted(self, original_status):
        self.application.status = CaseStatus.objects.get(status=original_status)
        self.application.save()

        mock_request = mock.Mock()
        mock_request.data = {"status": CaseStatusEnum.SURRENDERED}
        mock_request.user = self.exporter_user.baseuser_ptr
        assert self.permission_obj.has_object_permission(mock_request, None, self.application) is False

    @parameterized.expand(CaseStatusEnum.can_invoke_major_edit_statuses())
    def test_has_object_permission_set_applicant_editing_permitted(self, original_status):
        self.application.status = CaseStatus.objects.get(status=original_status)
        self.application.save()

        mock_request = mock.Mock()
        mock_request.data = {"status": CaseStatusEnum.APPLICANT_EDITING}
        mock_request.user = self.exporter_user.baseuser_ptr
        assert self.permission_obj.has_object_permission(mock_request, None, self.application) is True

    @parameterized.expand(non_major_editable_statuses)
    def test_has_object_permission_set_applicant_editing_not_permitted(self, original_status):
        self.application.status = CaseStatus.objects.get(status=original_status)
        self.application.save()

        mock_request = mock.Mock()
        mock_request.data = {"status": CaseStatusEnum.APPLICANT_EDITING}
        mock_request.user = self.exporter_user.baseuser_ptr
        assert self.permission_obj.has_object_permission(mock_request, None, self.application) is False

    @parameterized.expand(non_exporter_eligible_statuses)
    def test_has_object_permission_non_exporter_status_not_permitted(self, new_status):
        self.application.status = CaseStatus.objects.get(status=CaseStatusEnum.SUBMITTED)
        self.application.save()

        mock_request = mock.Mock()
        mock_request.data = {"status": new_status}
        mock_request.user = self.exporter_user.baseuser_ptr
        assert self.permission_obj.has_object_permission(mock_request, None, self.application) is False
