from django.urls import path, include

app_name = 'static'

urlpatterns = [
    path('countries/', include('static.countries.urls')),
    path('units/', include('static.units.urls')),
]
