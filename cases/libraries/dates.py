import datetime


def make_date_from_params(prefix, data):
    """
    Makes date from Lite forms DateInput data.
    """
    try:
        date = datetime.date(
            day=int(data.get(f"{prefix}_day")),
            month=int(data.get(f"{prefix}_month")),
            year=int(data.get(f"{prefix}_year")),
        )
        return date
    except (TypeError, ValueError):
        # Handle gracefully if no date or incorrect date data passed
        pass
