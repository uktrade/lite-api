from django.contrib import admin
from reversion.admin import VersionAdmin

from .models import AbstractApplication


@admin.register(AbstractApplication)
class ApplicationModelAdmin(VersionAdmin):

    pass
