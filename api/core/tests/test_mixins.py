import pytest

from reversion.errors import RegistrationError
from unittest import mock

from api.goods.models import Good
from test_helpers.clients import DataTestClient


class TrackableMixinTests(DataTestClient):

    @mock.patch("reversion.revisions.is_registered")
    def test_unregistered_model_raises_error(self, mock_is_registered):
        mock_is_registered.return_value = False
        good = Good(organisation=self.organisation, name="Rifle")

        with pytest.raises(RegistrationError):
            good.get_history("is_archived")

    def test_non_existent_field_raises_error(self):
        field = "non_existent_field"
        good = Good(organisation=self.organisation, name="Rifle")

        with pytest.raises(ValueError) as err:
            good.get_history(field)

        self.assertEqual(str(err.value), f"Model {good._meta.model} doesn't have the field {field}")
