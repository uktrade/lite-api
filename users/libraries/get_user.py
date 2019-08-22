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


def get_user_by_email(email):
    """
    Returns either an ExporterUser or a GovUser depending on the email given
    """
    try:
        return ExporterUser.objects.get(email=email)
    except ExporterUser.DoesNotExist:
        try:
            return GovUser.objects.get(email=email)
        except GovUser.DoesNotExist:
            raise NotFoundError({'user': 'User not found - ' + email})


def get_user_organisations(pk):
    try:
        user_organisation_relationships = UserOrganisationRelationship.objects.filter(user=pk)
        return [x.organisation for x in user_organisation_relationships]
    except UserOrganisationRelationship.DoesNotExist:
        raise NotFoundError({'user': 'User not found - ' + str(pk)})


def get_users_from_organisation(pk):
    try:
        user_organisation_relationships = UserOrganisationRelationship.objects.filter(organisation=pk)
        return [x.user for x in user_organisation_relationships]
    except UserOrganisationRelationship.DoesNotExist:
        raise NotFoundError({'organisation': 'Organisation not found - ' + str(pk)})
