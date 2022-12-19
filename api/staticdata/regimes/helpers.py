from api.core.exceptions import NotFoundError
from api.staticdata.regimes.models import RegimeEntry


def get_regime_entry(id):
    try:
        return RegimeEntry.objects.get(id=id)
    except RegimeEntry.DoesNotExist:
        raise NotFoundError({"regime_entry": f"'{id}' - Regime entry not found"})
