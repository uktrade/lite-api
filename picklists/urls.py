from django.urls import path

from picklists import views

app_name = 'picklist_items'

urlpatterns = [
    # ex: /picklist_items/
    # ex: /picklist_items/?type=
    path('', views.PickListItems.as_view(), name='picklist_items'),
    # ex: /picklist_items/<uuid:pk>/
    path('<uuid:pk>/', views.PicklistItemDetail.as_view(), name='picklist_item'),
]
