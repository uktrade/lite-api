from rest_framework.generics import RetrieveAPIView

from api.core.filters import ParentFilter
from api.core.tests.models import ChildModel
from api.core.tests.serializers import ChildModelSerializer


class MisconfiguredParentFilterView(RetrieveAPIView):
    filter_backends = (ParentFilter,)
    queryset = ChildModel.objects.all()


class ParentFilterView(RetrieveAPIView):
    filter_backends = (ParentFilter,)
    parent_filter_id_lookup_field = "parent_id"
    queryset = ChildModel.objects.all()
    serializer_class = ChildModelSerializer
