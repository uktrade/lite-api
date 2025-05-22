from django.db import models

from api.cases.enums import CaseTypeReferenceEnum


class ApplicationManifestFeatures(models.Model):
    case_type = models.CharField(max_length=255, choices=CaseTypeReferenceEnum.choices, unique=True)

    features = models.JSONField(default=dict)

    # Will be used later for checking whether we can issue a license.
    def has_feature(self, feature_name, default=None):
        return self.features.get(feature_name, default)
