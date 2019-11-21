from django.urls import path

from cases.generated_document import views

app_name = "generated_documents"

urlpatterns = [
    # ex: /cases/<uuid:pk>/generated-documents/
    path("", views.GeneratedDocuments.as_view(), name="generated_documents"),
]
