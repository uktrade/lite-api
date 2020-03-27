from test_helpers.test_endpoints.client import get


def call_endpoint(user, endpoint, times, times_key, is_gov=False):
    response = get(user, endpoint, is_gov)

    times[times_key] = response.elapsed.total_seconds()

    return response, times
