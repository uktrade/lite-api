from django.db import models


class ListField(models.TextField):
    description = 'Stores a list in the database'

    def __init__(self, *args, **kwargs):
        super(ListField, self).__init__(*args, **kwargs)

    def get_internal_type(self):
        return 'ListField'

    def to_python(self, value):
        if isinstance(value, str) or value is None:
            return value
        return str(value)

    def get_prep_value(self, value):
        value = super().get_prep_value(value)
        return self.to_python(value)
