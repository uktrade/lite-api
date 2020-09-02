from django.db.models.signals import post_save
from django.dispatch import receiver
from django_elasticsearch_dsl.registries import registry


@receiver(post_save)
def update_application_document(sender, **kwargs):
    app_label = sender._meta.app_label
    model_name = sender._meta.model_name
    instance = kwargs["instance"]

    if app_label == "applications":
        if model_name == "standardapplication" or model_name == "baseapplication":
            instances = instance.goods.all()
            for _instance in instances:
                registry.update(_instance)

        if model_name == "goodonapplication":
            registry.update(instance)

        if model_name == "goodonapplication":
            registry.update(instance)

        if model_name == "good":
            instances = instance.goods_on_application.all()
            for _instance in instances:
                registry.update(instance.application)

        if model_name == "partyonapplication":
            registry.update(instance.application)

    if app_label == "parties":
        if model_name == "party":
            for _instance in instance.parties_on_application:
                registry.update(_instance.application)

    if app_label == "organisations":
        if model_name == "organisation":
            instances = instance.cases.all()
            for _instance in instances:
                registry.update(_instance)
