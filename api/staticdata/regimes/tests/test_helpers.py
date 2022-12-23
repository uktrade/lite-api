import pytest
from test_helpers.clients import DataTestClient

from api.core.exceptions import NotFoundError
from api.staticdata.regimes.helpers import get_regime_entry
from api.staticdata.regimes.models import RegimeEntry


class RegimeHelperTests(DataTestClient):
    def test_get_regime_entry(self):

        regime = get_regime_entry(name="T1")
        self.assertEqual("T1", regime.name)

    def test_get_regime_entry_not_found(self):
        with pytest.raises(NotFoundError):
            get_regime_entry(name="Dummy")
