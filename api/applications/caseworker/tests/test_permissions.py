from unittest import mock
from parameterized import parameterized

from api.applications.caseworker.permissions import CaseStatusCaseworkerChangeable
from api.applications.tests.factories import StandardApplicationFactory
from api.core.constants import GovPermissions
from api.staticdata.statuses.enums import CaseStatusEnum
from api.staticdata.statuses.models import CaseStatus
from api.teams.models import Team
from api.teams.enums import TeamIdEnum
from api.users.models import Role


from test_helpers.clients import DataTestClient

permitted_statuses = list(
    set(CaseStatusEnum.all()) - set(CaseStatusEnum.terminal_statuses()) - set([CaseStatusEnum.APPLICANT_EDITING])
)


class TestChangeStatusCaseworkerChangeable(DataTestClient):

    def setUp(self):
        super().setUp()
        self.application = StandardApplicationFactory(status=CaseStatus.objects.get(status=CaseStatusEnum.SUBMITTED))
        self.permission_obj = CaseStatusCaseworkerChangeable()

    @parameterized.expand(permitted_statuses)
    def test_has_object_permission_permitted(self, case_status):
        mock_request = mock.Mock()
        mock_request.data = {"status": case_status}
        mock_request.user = self.gov_user.baseuser_ptr
        assert self.permission_obj.has_object_permission(mock_request, None, self.application) is True

    @parameterized.expand(CaseStatusEnum.terminal_statuses())
    def test_has_object_permission_original_status_terminal_no_user_permission(self, original_status):
        self.application.status = CaseStatus.objects.get(status=original_status)
        self.application.save()

        role = Role.objects.create(name="test")
        role.permissions.set([])
        self.gov_user.role = role
        self.gov_user.save()

        mock_request = mock.Mock()
        mock_request.user = self.gov_user.baseuser_ptr
        mock_request.data = {"status": CaseStatusEnum.OGD_ADVICE}
        assert self.permission_obj.has_object_permission(mock_request, None, self.application) is False

    @parameterized.expand(CaseStatusEnum.terminal_statuses())
    def test_has_object_permission_original_status_terminal_user_permitted(self, original_status):
        self.application.status = CaseStatus.objects.get(status=original_status)
        self.application.save()

        role = Role.objects.create(name="test")
        role.permissions.set([GovPermissions.REOPEN_CLOSED_CASES.name])
        self.gov_user.role = role
        self.gov_user.save()

        mock_request = mock.Mock()
        mock_request.user = self.gov_user.baseuser_ptr
        mock_request.data = {"status": CaseStatusEnum.OGD_ADVICE}
        assert self.permission_obj.has_object_permission(mock_request, None, self.application) is True

    def test_has_object_permission_new_status_applicant_editing(self):
        mock_request = mock.Mock()
        mock_request.user = self.gov_user.baseuser_ptr
        mock_request.data = {"status": CaseStatusEnum.APPLICANT_EDITING}
        assert self.permission_obj.has_object_permission(mock_request, None, self.application) is False

    def test_has_object_permission_new_status_finalised_user_permitted(self):
        self.gov_user.team = Team.objects.get(id=TeamIdEnum.LICENSING_UNIT)
        role = Role.objects.create(name="test")
        role.permissions.set([GovPermissions.MANAGE_LICENCE_FINAL_ADVICE.name])
        self.gov_user.role = role
        self.gov_user.save()

        mock_request = mock.Mock()
        mock_request.user = self.gov_user.baseuser_ptr
        mock_request.data = {"status": CaseStatusEnum.FINALISED}
        assert self.permission_obj.has_object_permission(mock_request, None, self.application) is True

    def test_has_object_permission_new_status_finalised_user_not_permitted(self):
        self.gov_user.team = Team.objects.get(id=TeamIdEnum.LICENSING_UNIT)
        role = Role.objects.create(name="test")
        role.permissions.set([])
        self.gov_user.role = role
        self.gov_user.save()

        mock_request = mock.Mock()
        mock_request.user = self.gov_user.baseuser_ptr
        mock_request.data = {"status": CaseStatusEnum.FINALISED}
        assert self.permission_obj.has_object_permission(mock_request, None, self.application) is False
