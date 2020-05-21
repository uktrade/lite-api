from cases.models import EnforcementCheckID


def enforcement_id_to_uuid(id):
    return EnforcementCheckID.objects.get(id=id).entity_id
