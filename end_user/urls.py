from django.urls import path

from end_user import views

app_name = 'end-users'

urlpatterns = [
    # ex: /end-users/ - Post an end user advisory enquiry query.
    path('', views.EUAEQueryList.as_view(), name='EUAE-query')
]
