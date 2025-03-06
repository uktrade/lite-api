class ManifestRegistry:

    def __init__(self):
        self.manifests = {}

    def register(self, application_type):
        def _register(cls):
            self.manifests[application_type] = cls()
            return cls

        return _register

    def get_manifest(self, application_type):
        return self.manifests[application_type]


application_manifest_registry = ManifestRegistry()
