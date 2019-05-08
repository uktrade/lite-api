from users.models import User


class CreateFirstAdminUser:
    def __init__(self, email, first_name, last_name, organisation):
        new_user = User(email=email,
                        first_name=first_name,
                        last_name=last_name,
                        organisation=organisation)
        new_user.set_password('password')
        new_user.save()
