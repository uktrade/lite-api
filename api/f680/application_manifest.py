from api.f680.models import F680Application
from api.f680.caseworker.serializers import F680ApplicationSerializer
from api.application_manifests.base import BaseManifest
from api.application_manifests.registry import application_manifest_registry
from api.cases.enums import ApplicationFeatures, CaseTypeSubTypeEnum
from gov_notify.enums import TemplateType


@application_manifest_registry.register(CaseTypeSubTypeEnum.F680)
class F680ApplicationManifest(BaseManifest):
    model_class = F680Application
    caseworker_serializers = {"view": F680ApplicationSerializer}
    features = {
        ApplicationFeatures.LICENCE_ISSUE: False,
        ApplicationFeatures.ROUTE_TO_COUNTERSIGNING_QUEUES: False,
    }
    ecju_max_days = 30
    notification_config = {
        "ecju_query": {"template": TemplateType.EXPORTER_F680_ECJU_QUERY, "frontend_url": "/"},
        "ecju_query_chaser": {
            "template": TemplateType.EXPORTER_F680_ECJU_QUERY_CHASER,
            "frontend_url": "/f680/{case_id}/summary/ecju-queries/",
        },
    }
