from api.applications.models import OpenApplication, StandardApplication
from api.applications.serializers.advice import (
    AdviceCreateSerializer,
    OpenAdviceCreateSerializer,
    AdviceViewSerializer,
    OpenAdviceViewSerializer,
)


class OpenApplicationManifest:
    application_model = OpenApplication

    serializers = {
        "advice_create": OpenAdviceCreateSerializer,
        "advice_view": OpenAdviceViewSerializer,
    }


class StandardApplicationManifest:
    application_model = StandardApplication

    serializers = {
        "advice_create": AdviceCreateSerializer,
        "advice_view": AdviceViewSerializer,
    }


manifest_registry = {
    "siel": StandardApplicationManifest,
    "oiel": OpenApplicationManifest,
}


def get_manifest(application):
    case_type_reference = application.case_type.reference
    return manifest_registry[case_type_reference]
