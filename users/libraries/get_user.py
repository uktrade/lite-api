from conf.exceptions import NotFoundError
from users.models import ExporterUser, GovUser, UserOrganisationRelationship


def get_user_by_pk(pk):
    """
    Returns either an ExporterUser or a GovUser depending on the PK given
    """
    try:
        return ExporterUser.objects.get(pk=pk)
    except ExporterUser.DoesNotExist:
        try:
            return GovUser.objects.get(pk=pk)
        except GovUser.DoesNotExist:
            raise NotFoundError({'user': 'User not found - ' + str(pk)})


def get_user_organisations(pk):
    try:
        user_organisation_relationships = UserOrganisationRelationship(user=pk)
        return [x.organisation for x in user_organisation_relationships.objects.all()]
    except UserOrganisationRelationship.DoesNotExist:
        raise NotFoundError({'user': 'User not found - ' + str(pk)})
