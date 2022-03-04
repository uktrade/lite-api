from django.urls import path

from api.goods import views

app_name = "goods"

urlpatterns = [
    path("", views.GoodList.as_view(), name="goods"),
    path("<uuid:pk>/", views.GoodOverview.as_view(), name="good"),
    path("<uuid:pk>/details/", views.GoodTAUDetails.as_view(), name="good_details"),
    path(
        "<uuid:pk>/document-availability/",
        views.GoodDocumentAvailabilityCheck.as_view(),
        name="good_document_availability",
    ),
    path(
        "<uuid:pk>/document-sensitivity/", views.GoodDocumentCriteriaCheck.as_view(), name="good_document_sensitivity"
    ),
    path("<uuid:pk>/documents/", views.GoodDocuments.as_view(), name="documents"),
    path(
        "<uuid:pk>/documents/<uuid:doc_pk>/",
        views.GoodDocumentDetail.as_view(),
        name="document",
    ),
    path(
        "<uuid:pk>/update-serial-numbers/",
        views.GoodUpdateSerialNumbers.as_view(),
        name="update_serial_numbers",
    ),
    path(
        "control-list-entries/<uuid:case_pk>/",
        views.GoodsListControlCode.as_view(),
        name="control_list_entries",
    ),
]
