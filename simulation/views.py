from django.http import HttpResponse
from django.views.generic import TemplateView


class DashboardView(TemplateView):
    template_name = "simulation/dashboard.html"
    
class AboutView(TemplateView):
    template_name = "simulation/about.html"