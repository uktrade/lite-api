from datetime import datetime, time

from background_task import background

SLA_UPDATE_TASK_HOUR = 18


@background(schedule=datetime.combine(datetime.now(), time(SLA_UPDATE_TASK_HOUR, 0, 0)))
def update_cases_sla():
    print("abc")
