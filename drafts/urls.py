from django.urls import path

from drafts import views

app_name = 'drafts'
urlpatterns = [
    path('', views.DraftList.as_view()),
    path('<uuid:pk>/', views.DraftDetail.as_view())
]
