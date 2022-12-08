from django.urls import path

from . import views


app_name = "regimes"

urlpatterns = [
    path("entries/<str:regime_type>/", views.EntriesView.as_view(), name="entries"),
    path("mtcr/entries/", views.MTCREntriesView.as_view(), name="mtcr_entries"),
    path("wassenaar/entries/", views.WassenaarEntriesView.as_view(), name="wassenaar_entries"),
]
