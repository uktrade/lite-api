from datetime import datetime, time

from background_task import background

from cases.models import Case

SLA_UPDATE_TASK_TIME = time(0, 0, 0)
SLA_UPDATE_CUTOFF_TIME = time(18, 0, 0)


@background(schedule=datetime.combine(datetime.now(), SLA_UPDATE_TASK_TIME))
def update_cases_sla():
    cases = Case.objects.filter(submitted_at__lt=datetime.combine(datetime.now(), SLA_UPDATE_CUTOFF_TIME))
    return cases
