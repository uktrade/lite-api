from test_helpers.test_endpoints.endpoint_functions import (
    application_get_endpoints,
    goods_get_endpoints,
    organisation_get_endpoints,
    end_user_advisories_get_endpoints,
    static_endpoints_get,
    users_get_endpoints,
    cases_get_endpoints,
    flags_get_endpoints,
    gov_users_get_endpoints,
    letter_templates_get_endpoints,
    picklist_get_endpoints,
    queues_get_endpoints,
    teams_get_endpoints,
)
from test_helpers.test_endpoints.user_setup import login_exporter, login_internal

times = {}


exporter = login_exporter()

times = application_get_endpoints(exporter, times)
times = goods_get_endpoints(exporter, times)
times = organisation_get_endpoints(exporter, times)
times = end_user_advisories_get_endpoints(exporter, times)
times = users_get_endpoints(exporter, times)

gov = login_internal()

times = cases_get_endpoints(gov, times)
times = flags_get_endpoints(gov, times)
times = gov_users_get_endpoints(gov, times)
times = letter_templates_get_endpoints(gov, times)
times = picklist_get_endpoints(gov, times)
times = queues_get_endpoints(gov, times)
times = teams_get_endpoints(gov, times)

times = static_endpoints_get(exporter, times)


print(times)

# TODO:
# 3. Split functionality up more
# 4. Move to unit tests
# 5. Caching of data such as standard_application, open_application, goods etc
# 6. Add functionality to run multiple tests based on parameters
# 7. Save output into a file for use later
