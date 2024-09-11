from django.core.management.base import BaseCommand

from gov_notify.email import NotifyEmail


class Command(BaseCommand):
    help = "Retrieves all template ids"

    def handle(self, *args, **options):
        for email_class in NotifyEmail.get_email_classes():
            self.stdout.write(f"{email_class.template_id}: {email_class.__name__}")
