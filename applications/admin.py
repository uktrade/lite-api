from django.contrib import admin
from reversion.admin import VersionAdmin

from .models import BaseApplication


@admin.register(BaseApplication)
class ApplicationModelAdmin(VersionAdmin):

    pass
