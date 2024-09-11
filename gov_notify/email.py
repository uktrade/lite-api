from django.core.exceptions import ImproperlyConfigured

from gov_notify.service import send_email


class NotifyEmail:
    _registered_email_classes = []

    def __init_subclass__(cls):
        cls._registered_email_classes.append(cls)

    @classmethod
    def get_email_classes(cls):
        return cls._registered_email_classes

    def get_email_recipient(self):
        raise NotImplementedError("Implement `get_email`")

    def get_data(self):
        raise NotImplementedError("Implement `get_data`")

    def send(self):
        template_id = getattr(self, "template_id", None)
        if not template_id:
            raise ImproperlyConfigured("`template_id` must be set")

        send_email(
            self.get_email_recipient(),
            self.template_id,
            self.get_data(),
        )
