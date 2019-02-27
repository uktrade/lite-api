from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

from drafts.models import Draft


@csrf_exempt
def drafts(request):
    if request.method == "POST":
        control_code = request.POST['control_code']
        activity = request.POST['activity']
        destination = request.POST['destination']
        usage = request.POST['usage']
        new_draft = Draft(control_code=control_code,
                          activity=activity,
                          destination=destination,
                          usage=usage)
        new_draft.save()
    else:
        return HttpResponse("dab GET mothercluckers")


@csrf_exempt
def draft(request, id):
    return HttpResponse("dab draft bitch" + id)
