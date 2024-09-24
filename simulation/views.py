from django.http import HttpResponse
from django.views.generic import TemplateView
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.shortcuts import render


class DashboardView(TemplateView):
    template_name = "simulation/dashboard.html"
    
class AboutView(TemplateView):
    template_name = "simulation/about.html"
    

@require_POST
def update_dashboard(request):
    bodyweight = float(request.POST.get('bodyweight', 0))
    distance = float(request.POST.get('distance', 0))
    relative_liver_mass = float(request.POST.get('RelativeLiverMass', 0))
    liver_glycogen_density = float(request.POST.get('liverGlycogenDensity', 0))
    relative_leg_muscle_mass = float(request.POST.get('RelativeLegMuscleMass', 0))
    leg_muscle_glycogen_density = float(request.POST.get('LegMuscleGlycogenDensity', 0))
    calories = bodyweight * distance
    return render(request, 'simulation/simulation_results.html', {'calories': calories})