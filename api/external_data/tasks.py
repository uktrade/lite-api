import logging
from django.conf import settings
from background_task import background

from django.utils import timezone

from pytz import timezone as tz
from datetime import datetime, time


from django.core.management import call_command


LOG_PREFIX = "update_sanction_search_index background task:"
SANCTIONS_UPDATE_SCHEDULE_TIME = time(8, 30, 0)
SANCTION_DATA_QUEUE = "load_sanction_data_queue"


@background(
    queue=SANCTION_DATA_QUEUE,
    schedule=datetime.combine(timezone.localtime(), SANCTIONS_UPDATE_SCHEDULE_TIME, tzinfo=tz(settings.TIME_ZONE)),
)
def update_sanction_search_index():
    """Update sanction index"""
    logging.info(f"{LOG_PREFIX} Update Started")
    call_command("ingest_sanctions", rebuild=True)
