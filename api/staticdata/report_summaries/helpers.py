from django.db.models import BinaryField, Case, When


def filtered_ordered_queryset(model_class, part_of_name):
    """
    Creates a queryset to get rows for the model where the
    'name' column contains the part_of_name parameter. The results
    are sorted so that entries where the name is prefixed by
    the part_of_name appear higher in the rankings and
    alphabetically after that.
    """
    queryset = model_class.objects.all()
    if part_of_name:
        queryset = queryset.filter(name__icontains=part_of_name)
        queryset = queryset.annotate(
            is_prefixed=Case(
                When(name__istartswith=part_of_name.lower(), then=True),
                default=False,
                output_field=BinaryField(),
            ),
        )
        queryset = queryset.order_by("-is_prefixed", "name")
    return queryset
