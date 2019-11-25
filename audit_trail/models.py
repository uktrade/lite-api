from django.db.models.signals import post_save
from actstream import action
from applications.models import OpenApplication


def my_handler(sender, instance, created, **kwargs):
    action.send(instance, verb='was saved')


post_save.connect(my_handler, sender=OpenApplication)
