from datetime import datetime, time

from background_task import background

SLA_UPDATE_TASK_TIME = time(24, 0, 0)


@background(schedule=datetime.combine(datetime.now(), SLA_UPDATE_TASK_TIME))
def update_cases_sla():
    print("abc")
