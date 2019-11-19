import reversion
from django.db import models

from cases.models import Case
from organisations.models import Organisation
from static.statuses.models import CaseStatus


@reversion.register()
class Query(Case):
    """
    Base query class
    """

    pass
