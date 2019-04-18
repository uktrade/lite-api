from django.contrib import admin
from reversion.admin import VersionAdmin

from users.models import User


@admin.register(User)
class UserModelAdmin(VersionAdmin):

    pass
