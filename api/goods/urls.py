from django.urls import path

from api.goods import views

app_name = "goods"

urlpatterns = [
    path("", views.GoodList.as_view(), name="goods"),
    path("<uuid:pk>/", views.GoodOverview.as_view(), name="good"),
    path("<uuid:pk>/attaching/", views.GoodAttaching.as_view(), name="good_attaching"),
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
        "document_internal_good_on_application/<str:goods_on_application_pk>/",
        views.DocumentGoodOnApplicationInternalView.as_view(),
        name="documents_good_on_application_internal",
    ),
    path(
        "document_internal_good_on_application_detail/<str:doc_pk>/",
        views.DocumentGoodOnApplicationInternalDetailView.as_view(),
        name="document_internal_good_on_application_detail",
    ),
]
