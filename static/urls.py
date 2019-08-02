from django.urls import path, include

app_name = 'static'

urlpatterns = [
    path('countries/', include('static.countries.urls')),
    path('denial-reasons/', include('static.denial_reasons.urls')),
    path('units/', include('static.units.urls')),
    path('statuses/', include('static.statuses.urls')),
]
