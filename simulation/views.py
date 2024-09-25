import datetime 
import numpy as np
import pandas as pd

from django.http import HttpResponse
from django.views.generic import TemplateView
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.shortcuts import render

import plotly.graph_objects as go
import plotly.offline as opy

from .import calculations, runners

class DashboardView(TemplateView):
    template_name = "simulation/dashboard.html"
    
class AboutView(TemplateView):
    template_name = "simulation/about.html"
    

def create_chart(df: pd.DataFrame, glycogen_buffer: float) -> go.Figure:
    # Create the plot
    trace = go.Scatter(x=df['Distance'], y=df['GlycogenLevelsPlusCarbs'], mode='lines', name='Glycogen storage')
    # Find the minimum y-value and the maximum x-value
    min_y = min(df['GlycogenLevelsPlusCarbs'].min() * 1.5, 0)
    max_x = df['Distance'].max()

    layout = go.Layout(
        hovermode='closest',
        plot_bgcolor='rgba(0,0,0,0)',  # this makes the plot area transparent
        paper_bgcolor='rgba(0,0,0,0)',  # this makes the area around the plot transparent
        xaxis=dict(
            title='km',
            showline=True,
        ),
        yaxis=dict(
            title='Glycogen storage in kcals',
            range=[min_y, df['GlycogenLevelsPlusCarbs'].max() * 1.1]  # this sets the y-axis range from min_y to the maximum y-value
        ),
        font=dict(
            color='white'
        ),
        shapes=[
            # This creates a rectangle from x=0 to x=max_x and from y=0 to y=min_y
            dict(
                type='rect',
                xref='x',
                yref='y',
                x0=0,
                y0=0,
                x1=max_x,
                y1=glycogen_buffer,
                fillcolor='rgba(255, 255, 0, 0.5)',  # this makes the fill color red with 50% opacity
                line=dict(width=0),  # this makes the border line invisible
                layer='below',
            ),
            dict(
                type='rect',
                xref='x',
                yref='y',
                x0=0,
                y0=0,
                x1=max_x,
                y1=min_y,
                fillcolor='rgba(255, 0, 0, 0.5)',  # this makes the fill color red with 50% opacity
                line=dict(width=0),  # this makes the border line invisible
                layer='below',
            ),
        ],
    )
    figure = go.Figure(data=[trace], layout=layout)

    # Convert the plot to HTML
    plot_div = opy.plot(figure, auto_open=False, output_type='div')
    
    return plot_div

@require_POST
def update_dashboard(request):
    slider_pace_in_min = float(request.POST.get('paceRange', 0))
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
    additional_carb_intake = float(request.POST.get('AdditionalCarbIntake', 0))
    total_available_glycogen = total_endogenous_glycogen_storage + additional_carb_intake * 4

    vo2 = calculations.convert_pace_to_vo2(slider_pace_in_min, vo2_max, bodyweight)
    intensity = vo2 / vo2_max
    pace_in_hours = calculations.convert_minutes_to_time(slider_pace_in_min)
    total_minutes = slider_pace_in_min * distance
    calories_burned = calculations.get_energy_expenditure(bodyweight, distance)
    glycogen_consumed = calculations.get_perc_glycogen_oxidation(vo2, vo2_max) * calories_burned
    percent_glycogen_consumed = glycogen_consumed / calories_burned * 100
    residual_glycogen = total_available_glycogen - glycogen_consumed
    finishing_time = calculations.convert_minutes_to_time(minutes=total_minutes, hours=True)
    glycogen_buffer = bodyweight * 3 * 4
    if residual_glycogen <= 0: 
        indication = "negative"
        interpretation = f"It is highly improbable that the race can be completed within the predicted finishing time of {finishing_time}, as the residual glycogen level at the end of the race is negative. This strongly suggests that the runner is likely to experience 'hitting the wall,' leading to substantial performance decline during the race, which would prevent achieving the projected time. A reduction in pace is advised to lower the rate of glycogen depletion throughout the race."
    elif residual_glycogen <= glycogen_buffer:
        indication = "warning"
        interpretation = f"There is uncertainty regarding the ability to complete the race within the predicted finishing time of {finishing_time}, as residual glycogen levels are below 3g per kg of body weight by the end of the race (equivalent to {round(glycogen_buffer)} kcals). Studies indicate that performance begins to decline before glycogen stores are completely exhausted, even in motivated endurance runners, at leg muscle glycogen concentrations approaching 3 to 5g per kg of body weight (see Karlsson J, Saltin B. Diet, muscle glycogen, and endurance performance. Journal of Applied Physiology. 1971;31:203–206.). It is recommended to either reduce the pace to conserve glycogen stores or increase glycogen availability through higher intial endogenous glycogen levels or carbohydrate supplementation during the race."
        if intensity > 0.8:
            additional_info = f"Additionally, the race is planned to be run at an intensity of {round(intensity * 100, 1)} %, as measured by the percentage of oxygen uptake (VO2) relative to maximal oxygen uptake capacity (VO2_max) which represents a considerable physiological challenge."
            interpretation = f"{interpretation} {additional_info}"
    else:
        indication = "positive"
        interpretation = f"It is possible that the race can be completed within the predicted finishing time of {finishing_time}, as residual glycogen levels are sufficiently high at the end of the race. However, other physiological factors may still prevent the predicted finishing time from being achieved."
        if intensity > 0.8:
            indication = "warning"
            additional_info = f"One contributing factor may be the intensity at which the race is planned to be run. An intensity of {round(intensity * 100, 1)} %, as measured by the percentage of oxygen uptake (VO2) relative to maximal oxygen uptake capacity (VO2_max), represents a considerable physiological challenge."
            interpretation = f"{interpretation} {additional_info}"

    df = calculations.time_series(
        distance=distance, 
        pace_in_min=slider_pace_in_min, 
        vo2_max=vo2_max, 
        bodyweight=bodyweight, 
        total_carb_intake=additional_carb_intake, 
        inital_endogenous_glycogen=total_endogenous_glycogen_storage
    )
    
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
                'finishing_time': finishing_time,
                'residual_glycogen': residual_glycogen,
                'intensity': intensity * 100,
                'vo2': vo2,
                'pace': pace_in_hours,
                'glycogen_consumed': glycogen_consumed,
                'percent_glycogen_consumed': percent_glycogen_consumed,
                'additional_carb_intake': additional_carb_intake,
                'total_available_glycogen': total_available_glycogen,
                'interpretation': interpretation,
                'indication': indication,
                'chart': create_chart(df, glycogen_buffer),
                })