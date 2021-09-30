from rest_framework import viewsets
from rest_framework.pagination import LimitOffsetPagination

from api.core.authentication import DataWorkspaceOnlyAuthentication
from api.organisations.models import Organisation
from api.organisations.serializers import OrganisationDetailSerializer
from api.parties.models import Party
from api.parties.serializers import PartyViewSerializer
from api.queues.models import Queue
from api.queues.serializers import QueueListSerializer
from api.teams.models import Team, Department
from api.teams.serializers import TeamReadOnlySerializer
from api.data_workspace.serializers import DepartmentSerializer


class OrganisationListView(viewsets.ReadOnlyModelViewSet):
    authentication_classes = (DataWorkspaceOnlyAuthentication,)
    serializer_class = OrganisationDetailSerializer
    pagination_class = LimitOffsetPagination
    queryset = Organisation.objects.all()


class PartyListView(viewsets.ReadOnlyModelViewSet):
    authentication_classes = (DataWorkspaceOnlyAuthentication,)
    serializer_class = PartyViewSerializer
    pagination_class = LimitOffsetPagination
    queryset = Party.objects.all()


class QueueListView(viewsets.ReadOnlyModelViewSet):
    authentication_classes = (DataWorkspaceOnlyAuthentication,)
    serializer_class = QueueListSerializer
    pagination_class = LimitOffsetPagination
    queryset = Queue.objects.all()


class TeamListView(viewsets.ReadOnlyModelViewSet):
    authentication_classes = (DataWorkspaceOnlyAuthentication,)
    serializer_class = TeamReadOnlySerializer
    pagination_class = LimitOffsetPagination
    queryset = Team.objects.all()


class DepartmentListView(viewsets.ReadOnlyModelViewSet):
    authentication_classes = (DataWorkspaceOnlyAuthentication,)
    serializer_class = DepartmentSerializer
    pagination_class = LimitOffsetPagination
    queryset = Department.objects.all()
