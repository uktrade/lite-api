from api.applications.models import StandardApplication
from api.applications.serializers.standard_application import StandardApplicationViewSerializer
from api.application_manifests.base import BaseManifest
from api.application_manifests.registry import application_manifest_registry
from api.cases.enums import ApplicationFeatures, CaseTypeSubTypeEnum
from gov_notify.enums import TemplateType


@application_manifest_registry.register(CaseTypeSubTypeEnum.STANDARD)
class StandardApplicationManifest(BaseManifest):
    model_class = StandardApplication
    caseworker_serializers = {"view": StandardApplicationViewSerializer}
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
