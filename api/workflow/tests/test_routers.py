import uuid

from django.test import SimpleTestCase

from parameterized import parameterized

from api.workflow.routers import (
    FlaggingRulesRouter,
    RoutingRulesRouter,
)


class TestFlaggingRulesRouter(SimpleTestCase):
    @parameterized.expand([l for l in FlaggingRulesRouter.Level])
    def test_get_criteria_function_not_implemented(self, level):
        router = FlaggingRulesRouter()
        with self.assertRaises(NotImplementedError):
            router.get_criteria_function(level, str(uuid.uuid4()))

    @parameterized.expand([l for l in FlaggingRulesRouter.Level])
    def test_get_criteria_function(self, level):
        router = FlaggingRulesRouter()
        rule_pk = uuid.uuid4()

        @router.register(level=level, rule_pk=rule_pk)
        def func():
            pass

        returned = router.get_criteria_function(level, rule_pk)
        self.assertEqual(returned, func)

    @parameterized.expand([l for l in FlaggingRulesRouter.Level])
    def test_has_criteria_function_not_existing(self, level):
        router = FlaggingRulesRouter()
        returned = router.has_criteria_function(level, str(uuid.uuid4()))
        self.assertFalse(returned)

    @parameterized.expand([l for l in FlaggingRulesRouter.Level])
    def test_has_criteria_function(self, level):
        router = FlaggingRulesRouter()
        rule_pk = uuid.uuid4()

        @router.register(level=level, rule_pk=rule_pk)
        def func():
            pass

        returned = router.has_criteria_function(level, rule_pk)
        self.assertTrue(returned)


class TestRoutingRulesRouter(SimpleTestCase):
    def test_get_criteria_function_not_implemented(self):
        router = RoutingRulesRouter()
        with self.assertRaises(NotImplementedError):
            router.get_criteria_function(str(uuid.uuid4()))

    def test_get_criteria_function(self):
        router = RoutingRulesRouter()
        rule_pk = uuid.uuid4()

        @router.register(rule_pk=rule_pk)
        def func():
            pass

        returned = router.get_criteria_function(rule_pk)
        self.assertEqual(returned, func)

    def test_has_criteria_function_not_existing(self):
        router = RoutingRulesRouter()
        returned = router.has_criteria_function(str(uuid.uuid4()))
        self.assertFalse(returned)

    def test_has_criteria_function(self):
        router = RoutingRulesRouter()
        rule_pk = uuid.uuid4()

        @router.register(rule_pk=rule_pk)
        def func():
            pass

        returned = router.has_criteria_function(rule_pk)
        self.assertTrue(returned)
