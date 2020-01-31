from django.db.models.signals import post_save
from django.dispatch import receiver

from applications.models import HmrcQuery


@receiver(post_save, sender=HmrcQuery)
def hmrc_query_save(instance: HmrcQuery, **kwargs):
    """
    Every time a HMRC Query is saved, run these automations
    """
    # If the goods are set to already departed, clear all existing sites and locations
    if instance.have_goods_departed:
        instance.application_sites.all().delete()
        instance.external_application_sites.all().delete()
