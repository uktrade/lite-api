from django.conf import settings
from static.control_list_entries.models import ControlListEntry


def parse_list_into_control_list_entries(worksheet):
    if not settings.SUPPRESS_TEST_OUTPUT:
        print(f"Seeding {worksheet.title}...")

    parents_at_depth = [None, None, None, None, None, None, None, None, None, None]
    current_depth = 1

    for row in worksheet.iter_rows(min_row=4):
        text, rating, is_decontrolled = None, None, False
        previous_depth = current_depth
        for cell in row:
            if cell.value is not None:
                if cell.column <= 10:
                    current_depth = cell.column
                    text = cell.value
                elif cell.column == 13:
                    rating = cell.value
                elif cell.column == 35:
                    is_decontrolled = cell.value.lower() == "x"
        if text is None:
            break

        if not is_decontrolled:
            if rating is None:
                raise Exception(f"Row {row[0].row} in {worksheet.title} doesn't have a rating and is controlled")

            if current_depth > previous_depth:
                parent = parents_at_depth[previous_depth]
            else:
                parent = parents_at_depth[current_depth - 1]

            # Build the new control list entry
            control_rating = ControlListEntry.objects.get_or_create(rating=rating, text=text, parent=parent)[0]

            control_rating.category = worksheet.title
            control_rating.save()

            parents_at_depth[current_depth] = control_rating
