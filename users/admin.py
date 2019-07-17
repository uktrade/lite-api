from django.contrib import admin
from reversion.admin import VersionAdmin

from users.models import ExporterUser, Notification


@admin.register(ExporterUser)
class UserModelAdmin(VersionAdmin):

    pass

@admin.register(Notification)
class NotificationModelAdmin(VersionAdmin):

    pass
