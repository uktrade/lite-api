from django.urls import path

from drafts import views

urlpatterns = [
    path('', views.drafts),
    path('<str:id>/', views.draft)
]
