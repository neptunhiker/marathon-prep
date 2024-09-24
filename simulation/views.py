import datetime 
import numpy as np

from django.http import HttpResponse
from django.views.generic import TemplateView
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.shortcuts import render

from .import calculations, runners

class DashboardView(TemplateView):
    template_name = "simulation/dashboard.html"
    
class AboutView(TemplateView):
    template_name = "simulation/about.html"
    

@require_POST
def update_dashboard(request):
    bodyweight = float(request.POST.get('bodyweight', 0))
    glycogen_buffer = bodyweight * 3 * 4  # 3g per kg of bodyweight (* 4 for kcals)
    distance = float(request.POST.get('distance', 0))
    vo2_max = float(request.POST.get('vo2_max', 0))
    relative_liver_mass = float(request.POST.get('RelativeLiverMass', 0))
    liver_mass = bodyweight * relative_liver_mass / 100
    liver_glycogen_density = float(request.POST.get('liverGlycogenDensity', 0))
    liver_glycogen_storage = liver_mass * liver_glycogen_density
    relative_leg_muscle_mass = float(request.POST.get('RelativeLegMuscleMass', 0))
    leg_muscle_mass = bodyweight * relative_leg_muscle_mass / 100
    leg_muscle_glycogen_density = float(request.POST.get('LegMuscleGlycogenDensity', 0))
    leg_muscle_glycogen_storage = leg_muscle_mass * leg_muscle_glycogen_density
    total_endogenous_glycogen_storage = liver_glycogen_storage + leg_muscle_glycogen_storage
    runner = runners.Runner(
        name="Bob the Runner",
        vo2_max=vo2_max,
        bodyweight=bodyweight,
        liver_mass_perc=relative_liver_mass,
        liver_glycogen_density=liver_glycogen_density,
        leg_muscles_mass_perc=relative_leg_muscle_mass,
        leg_muscles_glycogen_density=leg_muscle_glycogen_density,
        )
    intensities = [0.65, 0.70, 0.72, 0.74, 0.76, 0.78, 0.80, 0.85, 0.90]
    vo2s = [runner.vo2_max * intensity for intensity in intensities]
    sim_results = {}
    for vo2 in vo2s:
        pace_in_minutes = calculations.convert_vo2_to_pace_in_min(vo2, runner.vo2_max, runner.bodyweight)
        pace_in_hours = calculations.convert_minutes_to_time(pace_in_minutes)
        total_minutes = pace_in_minutes * distance
        calories_burned = calculations.get_energy_expenditure(runner.bodyweight, distance)
        glycogen_consumed = calculations.get_perc_glycogen_oxidation(vo2, runner.vo2_max) * calories_burned
        residual_glycogen = total_endogenous_glycogen_storage - glycogen_consumed
        sim_results[vo2] = {
            "percent_vo2_max": vo2 / runner.vo2_max * 100,
            "pace": pace_in_hours,
            "finishing_time": calculations.convert_minutes_to_time(minutes=total_minutes, hours=True),
            "glycogen_consumed": glycogen_consumed,
            "residual_glycogen": residual_glycogen
            }
    
    return render(request, 'simulation/simulation_results.html', 
                  {'glycogen_buffer': glycogen_buffer,
                   'distance': distance,
                   'bodyweight': bodyweight,
                   'calories_burned': calculations.get_energy_expenditure(bodyweight, distance),
                   'liver_mass': liver_mass,
                   'liver_glycogen_storage': liver_glycogen_storage,
                   'leg_muscle_mass': leg_muscle_mass,
                   'leg_muscle_glycogen_storage': leg_muscle_glycogen_storage,
                   'total_endogenous_glycogen_storage': total_endogenous_glycogen_storage,
                   'sim_results': sim_results,
                   })