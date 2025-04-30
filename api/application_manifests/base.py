class BaseManifest:
    exporter_serializers = {}
    caseworker_serializers = {}
    model_class = None
    # Use and add manifest features sparingly.
    # Consider if using an IF statement based on these flags is the best approach.
    # Maybe create a dedicated end point instead.
    features = {}
    email_templates = {}
    ecju_max_days = None

    def has_feature(self, feature):
        return self.features.get(feature, False)
