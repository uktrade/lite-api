from django.urls import path

from static.letter_layouts import views

app_name = 'letter_layouts'

urlpatterns = [
    # ex: /static/letter-layouts/
    path('', views.LetterLayoutsList.as_view(), name='letter_layouts'),
    # ex: /static/letter-layouts/<str:pk>/
    path('<str:pk>/', views.LetterLayoutDetail.as_view(), name='letter_layout'),
]
