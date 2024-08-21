from django.core.management.base import BaseCommand
from api.parties.models import Party
from api.audit_trail import service as audit_trail_service
from api.audit_trail.enums import AuditType
from api.users.models import BaseUser


class Command(BaseCommand):
    help = "Rename a field within party"

    def add_argument(self, parser):
        parser.add_argument("party_id", type=str, help="Party ID to be updated")

        parser.add_argument("field", type=str, help="The field you would like to update i.e address")

        parser.add_argument("value", type=str, help="the value to set the field to")

    def handle(self, *args, **kwargs):
        party_id = kwargs["party_id"]
        field = kwargs["field"]
        value = kwargs["value"]

        self.update_field_on_party(self, party_id, field, value)

    def update_field_on_party(self, party_id, field, value):
        party = Party.objects.get(party_id)
        system_user = BaseUser.objects.get(id="00000000-0000-0000-0000-000000000001")

        audit_trail_service.create(
            actor=system_user,
            verb=AuditType.DELETE_APPLICATION_DOCUMENT,
            target=party,
            payload={f"{field}": {"new": value, "old": party.__dict__.get(field)}},
        )

        party.update(**{self.field: self.value})
