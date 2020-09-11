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
    if app_label == "applications":
        if model_name in [
            "standardapplication",
            "baseapplication",
            "openapplication",
            "exhibitionclearanceapplication",
        ]:
            application = BaseApplication.objects.get(id=instance.id)
            registry.update(application)

    if app_label == "cases":
        if model_name == "case":
            base_application_id = BaseApplication.objects.get(id=instance.id)
            registry.update(base_application_id)

        if model_name == "caseassignment":
            base_application_id = BaseApplication.objects.get(id=instance.case.id)
            registry.update(base_application_id)

    if app_label == "goods":
        if model_name == "good":
            for goa in instance.goods_on_application.all():
                registry.update(goa.application)

    if app_label == "parties":
        if model_name == "party":
            for poa in instance.parties_on_application.all():
                registry.update(poa.application)

    if app_label == "organisations":
        if model_name == "organisation":
            for case in instance.cases.all():
                try:
                    base_application_id = BaseApplication.objects.get(id=case.id)
                    registry.update(base_application_id)
                except ObjectDoesNotExist:
                    pass
