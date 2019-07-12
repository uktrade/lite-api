from django.contrib import admin
from reversion.admin import VersionAdmin

from users.models import User, Notifications


@admin.register(User)
class UserModelAdmin(VersionAdmin):

    pass

@admin.register(Notifications)
class NotificationModelAdmin(VersionAdmin):

    pass
