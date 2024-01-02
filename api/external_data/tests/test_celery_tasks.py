from unittest import mock

from api.external_data.celery_tasks import update_sanction_search_index


@mock.patch("api.external_data.celery_tasks.call_command")
def test_update_sanction_search_index(mock_management_command):
    update_sanction_search_index.apply_async()
    mock_management_command.assert_called_once()
