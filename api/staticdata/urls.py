from django.urls import path, include

app_name = "staticdata"

urlpatterns = [
    path("case-types/", include("api.staticdata.case_types.urls")),
    path("control-list-entries/", include("api.staticdata.control_list_entries.urls")),
    path("private-venture-gradings/", include("api.staticdata.private_venture_gradings.urls")),
    path("countries/", include("api.staticdata.countries.urls")),
    path("f680-clearance-types/", include("api.staticdata.f680_clearance_types.urls")),
    path("decisions/", include("api.staticdata.decisions.urls")),
    path("letter-layouts/", include("api.staticdata.letter_layouts.urls")),
    path("denial-reasons/", include("api.staticdata.denial_reasons.urls")),
    path("units/", include("api.staticdata.units.urls")),
    path("statuses/", include("api.staticdata.statuses.urls")),
    path("upload-document-for-tests/", include("api.staticdata.upload_document_for_tests.urls")),
    path("missing-document-reasons/", include("api.staticdata.missing_document_reasons.urls")),
    path("item-types/", include("api.staticdata.good_item_types.urls")),
    path("trade-control/", include("api.staticdata.trade_control.urls")),
    path("regimes/", include("api.staticdata.regimes.urls")),
    path("report_summary/", include("api.staticdata.report_summaries.urls")),
]
