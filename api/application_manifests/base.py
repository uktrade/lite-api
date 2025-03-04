class BaseManifest:
    caseworker_serializers = {}
    model_class = None
    features = {}

    def has_feature(self, feature):
        return self.features.get(feature, False)
