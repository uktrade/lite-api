from background_task import background
from django.apps import apps
from django_elasticsearch_dsl.registries import registry

UPDATE_SEARCH_INDEX_QUEUE = "update_search_index_queue"


@background(queue=UPDATE_SEARCH_INDEX_QUEUE, schedule=0)
def update_search_index(model_pk_pairs):
    """Update the search index with instances of a model as specified by
    the supplied model_name and ids.
    """

    for model_name, pk in model_pk_pairs:
        model = apps.get_model(model_name)
        instance = model.objects.get(pk=str(pk))
        registry.update(instance)
