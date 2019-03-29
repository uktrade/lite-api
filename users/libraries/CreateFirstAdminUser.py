from users.models import User


class CreateFirstAdminUser:
    def __init__(self, email, organisation):
        new_user = User(email=email,
                        password=email,
                        organisation=organisation)

        new_user.save()
