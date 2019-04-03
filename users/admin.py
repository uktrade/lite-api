from django.contrib import admin
from reversion.admin import VersionAdmin

from .models import User


@admin.register(User)
class UserModelAdmin(VersionAdmin):

    pass
