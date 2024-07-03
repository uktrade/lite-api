from test_helpers.clients import DataTestClient

from api.users.models import (
    ExporterUser,
    GovUser,
)
from api.users.tests.factories import (
    BaseUserFactory,
    ExporterUserFactory,
    GovUserFactory,
)


class BaseUserTests(DataTestClient):
    def test_cast_to_user_type_ambiguous_type(self):
        exporteruser = ExporterUserFactory()
        govuser = GovUserFactory()
        base_user = BaseUserFactory(
            exporteruser=exporteruser,
            govuser=govuser,
        )
        with self.assertRaises(TypeError):
            base_user.cast_to_user_type()

    def test_cast_to_user_type_no_concrete_type(self):
        base_user = BaseUserFactory(
            exporteruser=None,
            govuser=None,
        )
        with self.assertRaises(TypeError):
            base_user.cast_to_user_type()

    def test_case_to_user_type_exporter_user(self):
        exporter_user = ExporterUserFactory()
        base_user = BaseUserFactory(
            exporteruser=exporter_user,
        )
        user = base_user.cast_to_user_type()
        self.assertIsInstance(user, ExporterUser)
        self.assertEqual(user, exporter_user)

    def test_case_to_user_type_gov_user(self):
        gov_user = GovUserFactory()
        base_user = BaseUserFactory(
            govuser=gov_user,
        )
        user = base_user.cast_to_user_type()
        self.assertIsInstance(user, GovUser)
        self.assertEqual(user, gov_user)
