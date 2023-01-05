from api.core.exceptions import NotFoundError
from api.staticdata.regimes.models import RegimeEntry


def get_regime_entry(name):
    try:
        return RegimeEntry.objects.get(name=name)
    except RegimeEntry.DoesNotExist:
        raise NotFoundError({"regime_entry": f"'{name}' - Regime entry not found"})
