from django.urls import path

from queries.end_user_advisories import views

app_name = 'end_user_advisories'

urlpatterns = [
    # ex: /queries/end-user-advisories/
    path('', views.EndUserAdvisoriesList.as_view(), name='end_user_advisories'),
    # ex: /queries/end-user-advisories/1234567890   - 10 digit int for eua primary key
    path('<int:pk>/', views.EndUserAdvisoriesDetail.as_view(), name='end_user_advisory'),
]
