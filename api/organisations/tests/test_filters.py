import pytest
from unittest import mock

from api.organisations.filters import CurrentExporterUserOrganisationFilter
from api.organisations.models import Site
from api.organisations.tests.factories import OrganisationFactory, SiteFactory
from api.users.tests.factories import ExporterUserFactory, UserOrganisationRelationshipFactory

pytestmark = pytest.mark.django_db


class TestCurrentExporterUserOrganisationFilter:

    def test_filter_queryset(self):
        filter_obj = CurrentExporterUserOrganisationFilter()
        organisation = OrganisationFactory()
        site = SiteFactory(organisation=organisation)
        # Create 10 Site records
        for i in range(10):
            SiteFactory()

        queryset = Site.objects.all()
        exporter_user = ExporterUserFactory()
        UserOrganisationRelationshipFactory(organisation=organisation, user=exporter_user)
        mock_request = mock.Mock()
        mock_request.META = {"HTTP_ORGANISATION_ID": str(organisation.id)}

        filtered_queryset = filter_obj.filter_queryset(mock_request, queryset, mock.Mock())
        assert list(filtered_queryset) == list(Site.objects.filter(organisation=organisation))
