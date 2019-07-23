from users.models import ExporterUser


class CreateFirstAdminUser:
    def __init__(self, email, first_name, last_name, organisation):
        new_user = ExporterUser(email=email,
                                first_name=first_name,
                                last_name=last_name,
                                organisation=organisation)
        new_user.set_password('password')
        new_user.save()
