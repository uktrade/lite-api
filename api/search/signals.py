from background_task.models import Task
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from api.applications.models import BaseApplication, GoodOnApplication
from api.goods.models import Good
from api.search.celery_tasks import update_search_index


@receiver(post_save)
def update_search_documents(sender, **kwargs):
    if not settings.LITE_API_ENABLE_ES or issubclass(sender, Task):
        return

    app_label = sender._meta.app_label
    model_name = sender._meta.model_name
    instance = kwargs["instance"]

    application_document_model = "applications.BaseApplication"
    product_document_model = "applications.GoodOnApplication"

    """
    To keep the index fresh we need to update them whenever the underlying data is updated.
    The immediate attributes of the index are handled by django_elasticsearch_dsl but
    additional changes are required to update the related models.
    The registry update code requires model corresponding to the index which is BaseApplication
    and GoodOnApplication in our case. We intercept the signals and update the index.
    """
    to_update = []

    if issubclass(sender, BaseApplication):
        to_update.append((application_document_model, instance.baseapplication.pk))

    if issubclass(sender, GoodOnApplication):
        to_update.append((product_document_model, instance.pk))

    if issubclass(sender, Good):
        for good_on_application in instance.goods_on_application.all():
            to_update.append((product_document_model, good_on_application.pk))

    try:
        if app_label == "cases" and model_name == "caseassignment":
            to_update.append((application_document_model, instance.case.baseapplication.pk))
        elif app_label == "cases" and model_name == "case":
            to_update.append((application_document_model, instance.baseapplication.pk))
        elif app_label == "goods" and model_name == "good":
            for good in instance.goods_on_application.all():
                to_update.append((application_document_model, good.application.pk))
        elif app_label == "parties" and model_name == "party":
            for party in instance.parties_on_application.all():
                to_update.append((application_document_model, party.application.pk))
        elif app_label == "organisations" and model_name == "organisation":
            for case in instance.cases.all():
                to_update.append((application_document_model, case.baseapplication.pk))
    except ObjectDoesNotExist:
        pass

    if to_update:
        to_update = [(model_name, str(pk)) for model_name, pk in to_update]
        update_search_index.delay(to_update)
