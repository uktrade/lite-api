from django.urls import path

from drafts import views

urlpatterns = [
    path('', views.drafts_list),
    path('<str:id>/', views.draft_detail)
]
