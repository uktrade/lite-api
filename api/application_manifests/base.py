
from api.cases.enums import ApplicationFeatures
class BaseManifest:
    def __init__(self):
        self.case_type_reference = None

    @property
    def _default_settings(self):
        return {
            ApplicationFeatures.LICENCE_ISSUE: False,
            ApplicationFeatures.ROUTE_TO_COUNTERSIGNING_QUEUES: False,
        }

