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
from api.data_workspace.serializers import DepartmentSerializer, SurveyResponseSerializer
from api.survey.models import SurveyResponse


class OrganisationListView(viewsets.ReadOnlyModelViewSet):
    authentication_classes = (DataWorkspaceOnlyAuthentication,)
    serializer_class = OrganisationDetailSerializer
    pagination_class = LimitOffsetPagination
    # We ensure that organisations with the same name always come out
    # in the same order by additionally ordering by created_at
    # and by id. If just name is used, the order is non-deterministic
    # when multiple organisations have the same name. This can mean the
    # same organisation being emitted on different pages, causing
    # primary key violations in Data Workspace.
    queryset = Organisation.objects.order_by("name", "created_at", "id")


class PartyListView(viewsets.ReadOnlyModelViewSet):
    authentication_classes = (DataWorkspaceOnlyAuthentication,)
    serializer_class = PartyViewSerializer
    pagination_class = LimitOffsetPagination
    # We ensure that parties with the same name always come out
    # in the same order by additionally ordering by created_at
    # and by id. If just name is used, the order is non-deterministic
    # when multiple parties have the same name. This can mean the
    # same party being emitted on different pages, causing
    # primary key violations in Data Workspace.
    queryset = Party.objects.order_by("name", "created_at", "id")


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


class SurveyResponseListView(viewsets.ReadOnlyModelViewSet):
    authentication_classes = (DataWorkspaceOnlyAuthentication,)
    serializer_class = SurveyResponseSerializer
    pagination_class = LimitOffsetPagination
    queryset = SurveyResponse.objects.all()
