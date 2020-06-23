from rest_framework import serializers


class EnumField(serializers.ChoiceField):
    def __init__(self, cls, **kwargs):
        self.cls = cls
        kwargs['choices'] = [(tag.value, tag.value) for tag in cls]
        print(kwargs["choices"])
        super(EnumField, self).__init__(**kwargs)

    def to_internal_value(self, data):
        try:
            return self.cls[data]
        except KeyError:
            self.fail('invalid_choice', input=data)
