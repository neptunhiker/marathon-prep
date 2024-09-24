import datetime

class Runner:

    def __init__(self, name: str, 
        vo2_max: float, 
        bodyweight: float, 
        liver_mass_perc: float=0.025, 
        liver_glycogen_density: float=360,
        leg_muscles_mass_perc: float=0.214, 
        leg_muscles_glycogen_density: float=80,
        birthdate: datetime.date=None, 
        ):
        self.name = name
        self.vo2_max = vo2_max
        self.birthdate = birthdate
        self.bodyweight = bodyweight
        self.liver_mass_perc = liver_mass_perc
        self.liver_glycogen_density = liver_glycogen_density
        self.leg_muscles_mass_perc = leg_muscles_mass_perc
        self.leg_muscles_glycogen_density = leg_muscles_glycogen_density
        self.current_glycogen_storage = self.initial_glycogen_storage
        self.injected_carbohydrates = 0
    
    @property
    def initial_liver_glyogen_storage(self):
        return self.bodyweight * self.liver_mass_perc * self.liver_glycogen_density

    @property
    def initial_leg_muscles_glycogen_storage(self):
        return self.bodyweight * self.leg_muscles_mass_perc * self.leg_muscles_glycogen_density

    @property
    def initial_glycogen_storage(self):
        return self.initial_liver_glyogen_storage + self.initial_leg_muscles_glycogen_storage

    @property
    def total_glycogen_storage(self):
        return self.initial_glycogen_storage + self.injected_carbohydrates * 4
    

    def inject_carbohydrates(self, amount_in_g: float):
        print("Injecting carbohydrates")
        self.injected_carbohydrates += amount_in_g
        self.current_glycogen_storage += amount_in_g * 4

    def consume_glycogen(self, amount_in_kcal: float):
        self.current_glycogen_storage -= amount_in_kcal
