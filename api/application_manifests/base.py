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

    def has_feature(self, feature_name, default=False):
        if hasattr(self, 'features'):
            return self.features.get(feature_name, default)
        return self._default_settings.get(feature_name, default)
