from django.contrib import admin
from reversion.admin import VersionAdmin

from .models import Organisation


@admin.register(Organisation)
class OrganisationModelAdmin(VersionAdmin):

    pass
