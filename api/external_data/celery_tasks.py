import logging

from celery import shared_task
from django.core.management import call_command


MAX_ATTEMPTS = 3
RETRY_BACKOFF = 180


@shared_task(
    autoretry_for=(Exception,),
    max_retries=MAX_ATTEMPTS,
    retry_backoff=RETRY_BACKOFF,
)
def update_sanction_search_index():
    """Update sanction index"""
    logging.info("update_sanction_search_index celery task: Update Started")
    call_command("ingest_sanctions", rebuild=True)
