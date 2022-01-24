from background_task import background
from django.apps import apps
from django_elasticsearch_dsl.registries import registry

UPDATE_SEARCH_INDEX_QUEUE = "update_search_index_queue"


@background(queue=UPDATE_SEARCH_INDEX_QUEUE, schedule=0)
def update_search_index(model_name, *ids):
    """Update the search index with instances of a model as specified by
    the supplied model_name and ids.
    """
    model = apps.get_model(model_name)

    for id_ in ids:
        instance = model.objects.get(pk=id_)
        registry.update(instance)
