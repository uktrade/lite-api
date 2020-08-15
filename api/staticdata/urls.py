from django.urls import path, include

app_name = "static"

urlpatterns = [
    path("case-types/", include("api.static.case_types.urls")),
    path("control-list-entries/", include("api.static.control_list_entries.urls")),
    path("private-venture-gradings/", include("api.static.private_venture_gradings.urls")),
    path("countries/", include("api.static.countries.urls")),
    path("f680-clearance-types/", include("api.static.f680_clearance_types.urls")),
    path("decisions/", include("api.static.decisions.urls")),
    path("letter-layouts/", include("api.static.letter_layouts.urls")),
    path("denial-reasons/", include("api.static.denial_reasons.urls")),
    path("units/", include("api.static.units.urls")),
    path("statuses/", include("api.static.statuses.urls")),
    path("upload-document-for-tests/", include("api.static.upload_document_for_tests.urls")),
    path("missing-document-reasons/", include("api.static.missing_document_reasons.urls")),
    path("item-types/", include("api.static.good_item_types.urls")),
    path("trade-control/", include("api.static.trade_control.urls")),
]
