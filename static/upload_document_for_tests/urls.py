from django.urls import path

from static.upload_document_for_tests import views

app_name = 'upload_document_for_tests'

urlpatterns = [
    path('', views.UploadDocumentForTests.as_view(), name='upload_document')
]
