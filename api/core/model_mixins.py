from itertools import zip_longest
from django.forms import model_to_dict
from reversion.models import Version


class Clonable:
    # Fields to exclude from cloning
    clone_exclusions = []
    # Global overrides for field values on cloned objects
    clone_overrides = {}
    # Field name mappings e.g. for mapping "good" to "good_id"
    clone_mappings = {}

    def clone(self, exclusions=None, **overrides):
        if not exclusions:
            exclusions = []
        all_exclusions = self.clone_exclusions + exclusions

        create_kwargs = model_to_dict(self, exclude=all_exclusions)

        for mapped_from, mapped_to in self.clone_mappings.items():
            create_kwargs[mapped_to] = create_kwargs.pop(mapped_from)

        if not overrides:
            overrides = {}
        all_overrides = {
            **self.clone_overrides,
            **overrides,
        }

        create_kwargs = {
            **create_kwargs,
            **all_overrides,
        }
        return self.__class__.objects.create(**create_kwargs)


class Trackable:
    """
    Mixin to be used by models that are registered with reversion.
    Provides helper methods that help handling various version of the model
    eg to retrieve history of a particular field value changes.
    """

    def get_history(self, field):
        raise NotImplementedError()


class TrackableMixin:

    def get_history(self, field):
        if not hasattr(self, field):
            raise ValueError(f"Model {self._meta.model} doesn't have the field {field}")

        # get older revisions first as we need to record the first instance a field is changed,
        # in subsequent revisions other fields might have changed and this field remained the same.
        versions = [
            v
            for v in Version.objects.get_for_object(self).order_by("revision__date_created")
            if v.field_dict[field] is not None
        ]

        version_history = []
        for current, next in zip_longest(versions, versions[1:], fillvalue=None):
            current_status = current.field_dict[field]
            next_status = next.field_dict[field] if next else None
            if current_status != next_status:
                version_history.append(current)

        return reversed(version_history)
