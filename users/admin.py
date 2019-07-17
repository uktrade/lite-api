from django.contrib import admin
from reversion.admin import VersionAdmin

from users.models import ExporterUser


@admin.register(ExporterUser)
class UserModelAdmin(VersionAdmin):

    pass
