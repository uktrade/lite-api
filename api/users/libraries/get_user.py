from typing import List

from api.core.exceptions import NotFoundError
from api.users.enums import UserStatuses
from api.users.models import ExporterUser, GovUser, UserOrganisationRelationship


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
            raise NotFoundError({"user": "User not found - " + str(pk)})


def get_exporter_user_by_email(email):
    """
    Returns an ExporterUser depending on the email given
    """
    try:
        return ExporterUser.objects.get(baseuser_ptr__email__iexact=email)
    except ExporterUser.DoesNotExist:
        raise NotFoundError({"user": "User not found - " + email})


def get_gov_user_by_email(email):
    """
    Returns a GovUser depending on the email given
    """
    try:
        return GovUser.objects.get(email__iexact=email)
    except GovUser.DoesNotExist:
        raise NotFoundError({"user": "User not found - " + email})


def get_user_organisations(pk):
    try:
        user_organisation_relationships = UserOrganisationRelationship.objects.filter(user=pk)
        return [x.organisation for x in user_organisation_relationships]
    except UserOrganisationRelationship.DoesNotExist:
        raise NotFoundError({"user": "User not found - " + str(pk)})


def get_users_from_organisation(pk) -> List[ExporterUser]:
    try:
        user_organisation_relationships = UserOrganisationRelationship.objects.filter(organisation=pk).order_by(
            "user__baseuser_ptr__first_name"
        )

        for relationship in user_organisation_relationships:
            relationship.user.status = relationship.status

        return [x.user for x in user_organisation_relationships]
    except UserOrganisationRelationship.DoesNotExist:
        raise NotFoundError({"organisation": "Organisation not found - " + str(pk)})


def get_user_organisation_relationship(user, organisation):
    try:
        return UserOrganisationRelationship.objects.get(user=user, organisation=organisation)
    except UserOrganisationRelationship.DoesNotExist:
        raise NotFoundError({"user_organisation_relationship": "User Organisation Relationship not found"})


def get_user_organisation_relationships(pk, status=None):
    """
    Returns relationships for an organisation filtered by status.
    """
    relationships = UserOrganisationRelationship.objects.filter(organisation=pk).order_by("user__email")
    if status:
        relationships = relationships.filter(status=UserStatuses.from_string(status))

    return relationships
