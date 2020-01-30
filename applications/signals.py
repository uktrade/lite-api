from django.db.models.signals import post_save
from django.dispatch import receiver

from applications.models import HmrcQuery


@receiver(post_save, sender=HmrcQuery)
def my_callback(instance: HmrcQuery, **kwargs):
    if instance.is_goods_departed:
        instance.application_sites.all().delete()
        instance.external_application_sites.all().delete()
