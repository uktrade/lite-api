from django.urls import path, include

app_name = "static"

urlpatterns = [
    path("case-types/", include("static.case_types.urls")),
    path("control-list-entries/", include("static.control_list_entries.urls")),
    path("countries/", include("static.countries.urls")),
    path("letter-layouts/", include("static.letter_layouts.urls")),
    path("denial-reasons/", include("static.denial_reasons.urls")),
    path("units/", include("static.units.urls")),
    path("statuses/", include("static.statuses.urls")),
    path("upload-document-for-tests/", include("static.upload_document_for_tests.urls")),
    path("missing-document-reasons/", include("static.missing_document_reasons.urls")),
]
