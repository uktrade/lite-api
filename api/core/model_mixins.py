from django.forms import model_to_dict


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
