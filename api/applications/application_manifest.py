from api.applications.models import StandardApplication
from api.applications.serializers.standard_application import StandardApplicationViewSerializer
from api.application_manifests.base import BaseManifest
from api.application_manifests.registry import application_manifest_registry
from api.cases.enums import (
    ApplicationFeatures,
    CaseTypeReferenceEnum,
)
from gov_notify.enums import TemplateType


@application_manifest_registry.register(CaseTypeReferenceEnum.EXPORT_LICENCE)
@application_manifest_registry.register(CaseTypeReferenceEnum.SIEL)
class ApplicationManifest(BaseManifest):
    model_class = StandardApplication
    # Warning: Caseworker and exporter currently share the same serializer which could lead
    # to internal data unintentional being shared with the exporter
    # TODO: LTD-6203 Create a dedicated serializer for the exporter
    caseworker_serializers = {"view": StandardApplicationViewSerializer}
    exporter_serializers = {"view": StandardApplicationViewSerializer}
    # Use and add manifest features sparingly.
    # Consider if using an IF statement based on these flags is the best approach.
    # Maybe create a dedicated end point instead.
    features = {
        ApplicationFeatures.LICENCE_ISSUE: True,
        ApplicationFeatures.ROUTE_TO_COUNTERSIGNING_QUEUES: True,
    }
    ecju_max_days = 20
    notification_config = {
        "ecju_query": {"template": TemplateType.EXPORTER_ECJU_QUERY, "frontend_url": "/"},
        "ecju_query_chaser": {
            "template": TemplateType.EXPORTER_ECJU_QUERY_CHASER,
            "frontend_url": "/applications/{case_id}/ecju-queries/",
        },
    }

    document_signing = {
        "signing_reason": "On behalf of the Secretary of State",
        "location": "Department for International Trade",
        "image_name": "dit_emblem.png",
    }
