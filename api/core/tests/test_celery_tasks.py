from test_helpers.clients import DataTestClient

from api.core import celery_tasks


class FlagsUpdateTest(DataTestClient):
    def test_debug_add(self):
        res = celery_tasks.debug_add(1, 2)
        assert res == 3

    def test_debug_exception(self):
        self.assertRaises(Exception, celery_tasks.debug_exception)
