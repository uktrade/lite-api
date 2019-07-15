def has_permission(user, permission):
    user_permissions = user.role.permissions.values_list('id', flat=True)
    return permission in user_permissions
