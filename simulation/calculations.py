import datetime 
import math
from .import runners

R_C = 120
R_F = 100
COEFF_1 = 0.73
COEFF_2 = 0.25
INTERCEPT = 0.01

def get_energy_expenditure(bodyweight: float, distance: float) -> float:
    """
    Get the energy expenditure of a runner with a specific bodyweight for a specific distance.

    return: energy expenditure in kcal
    """
    return bodyweight * distance

def get_perc_glycogen_oxidation(vo2: float, vo2_max: float) -> float:
    """
    Get the percentage of glycogen oxidation based on intensity of running measured as VO2 / VO2_max.

    return: Percentage of glycogen oxidation
    """
    intensity = vo2 / vo2_max
    return COEFF_1 * intensity**2 + COEFF_2 * intensity + INTERCEPT

def convert_oxygen_to_moles(oxygen_in_liters: float) -> float:
    """
    Convert liters of oxygen to moles.

    return: moles of oxygen
    """
    return oxygen_in_liters / 22.4

def get_hourly_oxygen_consumption(vo2: float, bodyweight: float) -> float:
    """
    Get an hourly oxygen consumption for a a runner running at VO2 having a specific bodyweight.
    
    return: hourly oxygen consumption in liters
    """
    return vo2 * bodyweight * 60 / 1000

def get_power_output(vo2: float, vo2_max: float, bodyweight: float) -> float:
    """
    Get the power output of a runner running at intensity VO2/VO2_max having a specific bodyweight.

    return: power output in kcal per hour
    """
    moles_of_oxygen = convert_oxygen_to_moles(get_hourly_oxygen_consumption(vo2, bodyweight))
    perc_glycogen_oxidation = get_perc_glycogen_oxidation(vo2, vo2_max)
    perc_fat_oxidation = 1 - perc_glycogen_oxidation
    return moles_of_oxygen / (perc_glycogen_oxidation / R_C + perc_fat_oxidation / R_F)

def convert_vo2_to_pace_in_min(vo2: float, vo2_max: float, bodyweight: float) -> float:
    """
    Get the corresponding pace for a runner with a specific bodyweight and VO2_max running at a given VO2 level.

    return: pace in minutes
    """
    power_output = get_power_output(vo2, vo2_max, bodyweight)
    return 60 / (power_output / bodyweight)

def convert_pace_to_vo2(pace_in_min: float, vo2_max: float, bodyweight: float) -> float:
    """
    Convert a pace in minutes for a given runner with a specific bodyweight and VO2_max to a corresponding level of VO2.

    return: VO2
    """
    power_output = 60 / pace_in_min * bodyweight
    p = (COEFF_2 / vo2_max + (bodyweight * 45) / (28 * power_output)) * (vo2_max**2 / COEFF_1)
    q = (INTERCEPT - 6) * (vo2_max**2 / COEFF_1)
    solution_1 = -p / 2 + ((p / 2)**2 - q)**0.5
    solution_2 = -p / 2 - ((p / 2)**2 - q)**0.5

    if 0 < solution_1 < vo2_max:
        return solution_1
    
    if 0 < solution_2 < vo2_max:
        return solution_2

    raise ValueError(f"Cannot find a solution greater than zero and less than the given VO2_max of {vo2_max} for a pace of {pace_in_min} minutes per kilometer.")

def convert_minutes_to_time(minutes: float, hours: bool=False) -> datetime.time:
    """
    Convert minutes into a datetime.time object

    return: The converted minutes in datetime.time
    """
    hours = math.floor(minutes / 60)
    mins = math.floor(minutes % 60)
    seconds = int(minutes % math.floor(minutes) * 60)  # use np.round once imported
    time = datetime.time(hours, mins, seconds)
    if hours:
        return time.strftime("%H:%M:%S")
    else:
        return time.strftime("%M:%S")
    
def print_marathon_predictions(runner: runners.Runner) -> None:

    intensities = [0.6 + i * 0.05 for i in range(7)]

    print("MARATHON PREDICTIONS")
    for intensity in intensities:
        vo2 = intensity * runner.vo2_max
        pace_in_minutes = convert_vo2_to_pace_in_min(vo2, runner.vo2_max, runner.bodyweight)
        expected_energy_consumption = 43 * runner.bodyweight
        perc_glycogen_oxidation = get_perc_glycogen_oxidation(vo2, runner.vo2_max)
        abs_glycogen_consumption = int(expected_energy_consumption * perc_glycogen_oxidation)  # use np.round when available
        residual_glycogen_storage = runner.total_glycogen_storage - abs_glycogen_consumption
        print(f"Intensity: {intensity * 100} %")
        print(f"VO2: {vo2} mL min^(-1) kg^(-1)")
        print(f"Pace: {convert_minutes_to_time(pace_in_minutes)}")
        print(f"Projected finish time: {convert_minutes_to_time(43 * pace_in_minutes)}")
        print(f"Expected energy expenditure: {43 * runner.bodyweight} kcals")
        print(f"Expected relative glycogen oxidation: {get_perc_glycogen_oxidation(vo2, runner.vo2_max) * 100} %")
        print(f"Expected absolute glycogen depletion: {abs_glycogen_consumption} kcals")
        print(f"Initial glycogen storage: {runner.initial_glycogen_storage} kcals")
        print(f"Additional glycogen inejction: {runner.injected_carbohydrates * 4} kcals")
        print(f"Total available glycogen for the race: {runner.total_glycogen_storage} kcals")
        print(f"Expected residual glycogen storage at the end of the race: {residual_glycogen_storage} kcals")
        if residual_glycogen_storage > 4 * runner.bodyweight * 4: 
            print(f"Runner can safely complete the race with target intensity of {intensity * 100} % and pace of {convert_minutes_to_time(pace_in_minutes)}.")
        elif residual_glycogen_storage > 0:
            print(f"Runner may be able to complete the race with target intensity of {intensity * 100} % and pace of {convert_minutes_to_time(pace_in_minutes)}, but the residual glycogen level of {residual_glycogen_storage} kcals ({residual_glycogen_storage / 4} g) falls already in the buffer area of 4g per kg of bodyweight.")
        else:
            print(f"It is very unlikely that the runner will be able to finish the race with target intensity of {intensity * 100} % and pace of {convert_minutes_to_time(43 * pace_in_minutes)}.")
        print()


# to be continued:
# create class to simulate marathon with input Runner, PacingStrategy, and NutritionStrategy (-> pandas df)

if __name__ == "__main__":
    from runners import Runner

    seb = Runner("Seb", 55, datetime.date(1984, 1, 22), 73)

    seb.inject_carbohydrates(150)

    print_marathon_predictions(runner=seb)

    paces = [4 + i / 5 for i in range(20)]
    
    for pace in paces:
        converted_vo2 = convert_pace_to_vo2(pace, seb.vo2_max, seb.bodyweight)
        energy_expenditure = seb.bodyweight * 60 / pace
        liters_oxygen_per_hour = energy_expenditure / 5
        liters_oxygen_per_minute = liters_oxygen_per_hour / 60
        simple_vo2 = liters_oxygen_per_minute / seb.bodyweight *1000
        print(int((converted_vo2-simple_vo2) * 100))        