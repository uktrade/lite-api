from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.translation import gettext_lazy as _
from model_utils.fields import AutoCreatedField, AutoLastModifiedField


class CreatedAt(models.Model):
    created_at = AutoCreatedField(_("created_at"))

    class Meta:
        abstract = True


class TimestampableModel(CreatedAt):
    updated_at = AutoLastModifiedField(_("updated_at"))

    class Meta:
        abstract = True


def prefetch_generic_relations(qs):  # noqa
    """
    Prefetches the models attributed to all generic fields in a queryset

    From https://djangosnippets.org/snippets/2492/ with some tweaks.
    """

    def get_content_type(content_type_id, cache={}):  # noqa
        if content_type_id in cache:
            return cache[content_type_id]
        content_type = ContentType.objects.get_for_id(content_type_id)
        cache[content_type_id] = content_type
        return content_type

    gfks = {}
    for name, gfk in qs.model.__dict__.items():
        if not isinstance(gfk, GenericForeignKey):
            continue
        gfks[name] = gfk

    data = {}
    for weak_model in qs:
        for gfk_name, gfk_field in gfks.items():
            fields = gfk_field.model._meta.get_fields()
            field = None
            for f in fields:
                if f.name == gfk_field.ct_field:
                    field = f
            if field is None:
                continue
            related_content_type_id = getattr(weak_model, field.get_attname())
            if not related_content_type_id:
                continue
            related_content_type = get_content_type(related_content_type_id)
            related_object_id = getattr(weak_model, gfk_field.fk_field)

            if related_content_type not in data.keys():
                data[related_content_type] = []
            data[related_content_type].append(related_object_id)

    for content_type, object_ids in data.items():
        model_class = content_type.model_class()
        models = prefetch_generic_relations(model_class.objects.filter(pk__in=object_ids))

        for model in models:
            for weak_model in qs:
                for gfk_name, gfk_field in gfks.items():
                    fields = gfk_field.model._meta.get_fields()
                    field = None
                    for f in fields:
                        if f.name == gfk_field.ct_field:
                            field = f
                    if field is None:
                        continue
                    related_content_type_id = getattr(weak_model, field.get_attname())
                    if not related_content_type_id:
                        continue
                    related_content_type = get_content_type(related_content_type_id)
                    related_object_id = getattr(weak_model, gfk_field.fk_field)

                    if str(related_object_id) != str(model.pk):
                        continue
                    if related_content_type != content_type:
                        continue
                    setattr(weak_model, gfk_name, model)
    return qs
