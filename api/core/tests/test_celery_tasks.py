from test_helpers.clients import DataTestClient

from api.cases.tests.factories import CaseFactory
from api.core import celery_tasks


class FlagsUpdateTest(DataTestClient):
    def test_debug_add(self):
        res = celery_tasks.debug_add(1, 2)
        assert res == 3

    def test_debug_count_cases(self):
        CaseFactory()
        res = celery_tasks.debug_count_cases()
        assert res == 1

    def test_debug_exception(self):
        self.assertRaises(Exception, celery_tasks.debug_exception)
