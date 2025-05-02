class BaseManifest:
    exporter_serializers = {}
    caseworker_serializers = {}
    model_class = None
    features = {}
    email_templates = {}
    ecju_max_days = None

    def has_feature(self, feature):
        return self.features.get(feature, False)
