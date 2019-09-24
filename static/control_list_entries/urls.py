from django.urls import path

from static.control_list_entries import views

app_name = 'control_list_entries'

urlpatterns = [
    # ex: /static/control-list-entries/
    path('', views.ControlListEntriesList.as_view(), name='control_list_entries'),
    # ex: /static/control-list-entries/<str:rating>/
    path('<str:rating>/', views.ControlListEntryDetail.as_view(), name='control_list_entry'),
    # ex: /static/control-list-entries/upload_data/
    path('upload-data/', views.UploadData.as_view(), name='upload_data'),
]
