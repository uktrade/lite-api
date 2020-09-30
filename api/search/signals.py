from django.core.exceptions import ObjectDoesNotExist
from django.db.models.signals import post_save
from django.dispatch import receiver
from django_elasticsearch_dsl.registries import registry

from api.applications.models import BaseApplication


@receiver(post_save)
def update_application_document(sender, **kwargs):
    app_label = sender._meta.app_label
    model_name = sender._meta.model_name
    instance = kwargs["instance"]

    """
    To keep the index fresh we need to update them whenever the underlying data is updated.
    The immediate attributes of the index are handled by django_elasticsearch_dsl but
    additional changes are required to update the related models.

    The registry update code requires model corresponding to the index which is BaseApplication
    in our case. We intercept the signals and update the index.
    """
    if issubclass(sender, BaseApplication):
        registry.update(instance.baseapplication)

    try:
        if app_label == "cases" and model_name == "caseassignment":
            registry.update(instance.case.baseapplication)
        elif app_label == "cases" and model_name == "case":
            registry.update(instance.baseapplication)
        elif app_label == "goods" and model_name == "good":
            for good in instance.goods_on_application.all():
                registry.update(good.application)
        elif app_label == "parties" and model_name == "party":
            for party in instance.parties_on_application.all():
                registry.update(party.application)
        elif app_label == "organisations" and model_name == "organisation":
            for case in instance.cases.all():
                registry.update(case.baseapplication)
    except ObjectDoesNotExist:
        pass
