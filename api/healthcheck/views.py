from health_check.views import MainView
from django.http import HttpResponse


class HealthCheckPingdomView(MainView):
    template_name = "pingdom.xml"

    def render_to_response(self, context, status):
        context["errored_plugins"] = [plugin for plugin in context["plugins"] if plugin.errors]
        context["total_response_time"] = sum([plugin.time_taken for plugin in context["plugins"]])
        return super().render_to_response(context=context, status=status, content_type="text/xml")


class ServiceAvailableHealthCheckView(MainView):
    def get(self, request, *args, **kwargs):
        status = 200
        return self.render_to_response(status)

    def render_to_response(self, status):
        return HttpResponse("STATUS OK" if status == 200 else "STATUS NOT OK", status=status)
