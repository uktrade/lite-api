import uuid

import factory

from gov_notify.models import GovNotifyTemplate


class GovNotifyTemplateFactory(factory.django.DjangoModelFactory):
    template_id = uuid.uuid4()

    class Meta:
        model = GovNotifyTemplate
