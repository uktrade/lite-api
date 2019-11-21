import reversion

from cases.models import Case


@reversion.register()
class Query(Case):
    """
    Base query class
    """

    pass
