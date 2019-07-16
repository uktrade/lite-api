from django.contrib import admin
from reversion.admin import VersionAdmin

from users.models import User, Notification


@admin.register(User)
class UserModelAdmin(VersionAdmin):

    pass

@admin.register(Notification)
class NotificationModelAdmin(VersionAdmin):

    pass
