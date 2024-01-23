from celery import shared_task
from django.apps import apps
from django_elasticsearch_dsl.registries import registry

UPDATE_SEARCH_INDEX_QUEUE = "update_search_index_queue"


MAX_ATTEMPTS = 3
RETRY_BACKOFF = 180


@shared_task(
    autoretry_for=(Exception,),
    max_retries=MAX_ATTEMPTS,
    retry_backoff=RETRY_BACKOFF,
)
def update_search_index(model_pk_pairs):
    """Update the search index with instances of a model as specified by
    the supplied model_name and ids.
    """

    for model_name, pk in model_pk_pairs:
        model = apps.get_model(model_name)
        instance = model.objects.get(pk=pk)
        registry.update(instance)
