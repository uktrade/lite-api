from cases.libraries.get_case import get_case
from cases.serializers import CaseFlagsAssignmentSerializer
from goods.libraries.get_good import get_good
from goods.serializers import GoodFlagsAssignmentSerializer


def get_object_of_level(level, pk):
    if level == 'goods':
        return get_good(pk)
    elif level == 'cases':
        return get_case(pk)


def flag_assignment_serializer(level, data, context):
    if level == 'goods':
        return GoodFlagsAssignmentSerializer(data=data, context=context)
    elif level == 'cases':
        return CaseFlagsAssignmentSerializer(data=data, context=context)
