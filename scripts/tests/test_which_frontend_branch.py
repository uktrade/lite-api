from parameterized import parameterized

from ..which_frontend_branch import get_frontend_branch
from test_helpers.clients import DataTestClient


class WhichFrontendBranchTest(DataTestClient):

    @parameterized.expand(
        [
            "LTD-12345-branch",
            "completely-different-branch",
        ]
    )
    def test_default_branch(self, non_specific_branch_name):
        self.assertEqual(get_frontend_branch(non_specific_branch_name), "dev")

    @parameterized.expand(
        [
            "dev",
            "uat",
            "master",
        ]
    )
    def test_main_branches(self, main_branch_name):
        self.assertEqual(get_frontend_branch(main_branch_name), main_branch_name)

    @parameterized.expand(
        [
            ("hotfix-uat", "uat"),
            ("hotfix-uat-more-words", "uat"),
            ("hotfix-master", "master"),
            ("hotfix-master-more-words", "master"),
        ]
    )
    def test_hotfix_branches(self, hotfix_branch_name, expected_target):
        self.assertEqual(get_frontend_branch(hotfix_branch_name), expected_target)
