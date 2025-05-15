from api.organisations.models import Organisation
from django.db import models
from waffle.models import AbstractUserFlag


class FeatureFlag(AbstractUserFlag):

    organisations = models.ManyToManyField(
        Organisation,
        blank=True,
        help_text=("Activate this flag for users in these organisations."),
    )

    def is_active_for_user(self, user):
        print(f"running is_active_for_user {user.pk}")
        is_active = super(FeatureFlag, self).is_active_for_user(user)
        if is_active:
            print("Already active for user")
            return is_active

        if user.pk in self._get_organisation_users():
            print("Wasnt active but user is in organisation so now is")
            return True

    def _get_organisation_users(self):
        organisations = self.organisations.all()
        print(f"Organisations are {organisations}")
        users = sum([organisation.get_users() for organisation in organisations], [])
        print(f"Users in those are {users}")
        return [user.pk for user in users]
