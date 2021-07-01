from django.conf import settings
from api.staticdata.control_list_entries.models import ControlListEntry

MAX_DEPTH = 10
RATING_COLUMN = 13
CONTROLLED_COLUMN = 35


def parse_list_into_control_list_entries(worksheet):
    if not settings.SUPPRESS_TEST_OUTPUT:
        print(f"Seeding {worksheet.title}...")

    current_depth = 1
    parents_at_depth = [None] * MAX_DEPTH

    for row in worksheet.iter_rows(min_row=4):
        text, rating, controlled = None, None, True
        previous_depth = current_depth
        for cell in row:
            if cell.value is not None:
                if cell.column <= MAX_DEPTH:
                    current_depth = cell.column
                    text = cell.value
                elif cell.column == RATING_COLUMN:
                    rating = cell.value
                elif cell.column == CONTROLLED_COLUMN:
                    controlled = cell.value.lower() != "x"

        if text is None:
            break

        if controlled:
            if rating is None:
                raise Exception(f"Row {row[0].row} in {worksheet.title} doesn't have a rating and is controlled")

            if current_depth > previous_depth:
                parent = parents_at_depth[previous_depth]
            else:
                parent = parents_at_depth[current_depth - 1]

            # Build the new control list entry if it doesn't exist
            control_rating = ControlListEntry.objects.get_or_create(rating=rating, parent=parent)[0]

            control_rating.category = worksheet.title
            control_rating.text = text
            control_rating.controlled = True
            control_rating.save()

            parents_at_depth[current_depth] = control_rating
        else:
            try:
                control_rating = ControlListEntry.objects.get(rating=rating)
                control_rating.text = text
                control_rating.controlled = False
                control_rating.save()
            except ControlListEntry.DoesNotExist:
                pass
