from static.control_list_entries.models import ControlListEntry


def parse_list_into_control_list_entries(worksheet):
    print(f'Seeding {worksheet.title}...')

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
                    is_decontrolled = cell.value.lower() == 'x'
        if text is None:
            break

        if current_depth > previous_depth:
            parent = parents_at_depth[previous_depth]
        else:
            parent = parents_at_depth[current_depth - 1]

        control_rating = ControlListEntry.create_or_update(rating=rating,
                                                           text=text,
                                                           parent=parent,
                                                           is_decontrolled=is_decontrolled)

        parents_at_depth[current_depth] = control_rating
