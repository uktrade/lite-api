from api.cases.enums import ApplicationFeatures


class BaseManifest:
    def __init__(self):
        self.case_type_reference = None

    @property
    def _default_settings(self):
        return {
            ApplicationFeatures.LICENCE_ISSUE.value: False,
            ApplicationFeatures.ROUTE_TO_COUNTERSIGNING_QUEUES.value: False,
        }

    def has_feature(self, feature_name, default=False):
        features = getattr(self, "features", None)
        return features.get(feature_name, default) if features else self._default_settings.get(feature_name, default)
