from django.db import models, transaction

from licences.enums import LicenceStatus


class LicenceManager(models.Manager):
    def new(self, application_reference, validated_data):
        """
        Override create in order to avoid creating multiple draft versions of a Licence
        """
        if LicenceStatus(validated_data["status"]) == LicenceStatus.DRAFT:
            status = validated_data.pop("status")
            application = validated_data.pop("application")

            with transaction.atomic():
                """Lock to avoid race conditions"""
                try:
                    licence = self.model.objects.get(status=status, application=application)
                    for field, value in validated_data.items():
                        setattr(licence, field, value)
                    licence.save()
                except self.model.DoesNotExist:
                    from licences.helpers import get_reference_code
                    reference_code = get_reference_code(application_reference)
                    licence = self.model.objects.create(status=status, application=application, reference_code=reference_code, **validated_data)
                return licence

        return self.create(validated_data)

    def get_open_licence(self, application):
        return self.get(application=application, status__in=[LicenceStatus.ISSUED.value, LicenceStatus.REINSTATED.value])
