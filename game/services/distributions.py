import random


# defining the toys here rather than in the admin page to avoid potential interference when two players are using the game
toy_settings = [
    {'name': 'Kite',
     'distribution': [0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
     "default": True,
     "Price": 17,
     "Cost": 8},

    {'name': 'Yo-Yo',
     'distribution': [0.25, 0.275, 0.3, 0.325, 0.35, 0.375, 0.4, 0.425, 0.45, 0.475, 0.5, 0.525, 0.55, 0.575, 0.6, 0.625, 0.65, 0.675, 0.7, 0.725],
     "default": True,
     "Price": 10,
     "Cost": 3},

    {'name': 'Bike',
     'distribution': [0, 0, 0.1, 0.2, 0.2, 0.25, 0.25, 0.3, 0.3, 0.3, 0.4, 0.5, 0.75, 0.75, 0.85, 1, 1, 1, 1, 1],
     "default": True,
     "Price": 27,
     "Cost": 12},

    {'name': 'Racecar',
     'distribution': [0.1, 0.1, 0.15, 0.25, 0.25, 0.3, 0.3, 0.3, 0.3, 0.3, 0.4, 0.5, 0.75, 0.75, 0.85, 1.0, 1.0, 1.0, 1.0, 1.0],
     "default": False,
     "Price": 32,
     "Cost": 15},

    {'name': 'Doll',
     'distribution': [0.45, 0.45, 0.45, 0.45, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.55, 0.55, 0.55, 0.55],
     "default": False,
     "Price": 2.5,
     "Cost": 1},

    {'name': 'TeddyBear',
    'distribution' : [0.05, 0.05, 0.15, 0.25, 0.25, 0.3, 0.3, 0.35, 0.35, 0.35, 0.45, 0.55, 0.8, 0.8, 0.9, 1.0, 1.0, 1.0, 1.0, 1.0],
    "default": False,
    "Price": 25,
    "Cost": 10},
]




def pick_from_distribution(toy):
    """
    Picks a demand percentage based on index position.
    Assumes distribution is a list of probabilities.
    """

    weights = toy.demand_distribution_json

    if not weights:
        raise ValueError(f"No demand distribution for toy: {toy.name}")

    steps = len(weights)

    roll_index = random.randint(0, steps - 1)

    demand_fraction = weights[roll_index]

    return roll_index + 1, demand_fraction



def pick_from_disaster_distribution(insurance_event):
    """
    Picks a demand percentage based on index position.
    Assumes distribution is a list of probabilities.
    """

    weights = insurance_event.demand_distribution_json

    if not weights:
        raise ValueError(f"No demand distribution for event: {insurance_event.name}")

    steps = len(weights)

    roll_index = random.randint(0, steps - 1)

    disaster_cost = weights[roll_index]

    return roll_index + 1, disaster_cost


def pick_interest_rate(rate_profile):
    distribution = rate_profile.rate_distribution_json
    rates  = [item[0] for item in distribution]
    weights = [item[1] for item in distribution]
    return random.choices(rates, weights=weights, k=1)[0]

def calculate_probability_of_new_product_success(cumulative_spend, m, b):
    # y = mx + b
    prob = (m * cumulative_spend) + b
    return prob

def pick_from_new_product_distribution():
    pick = random.randint(1, 100)
    return pick


def calculate_product_chances(cumulative_spend, slope_racecar, racecar_intercept, slope_doll, doll_peak, doll_intercept, toys):
    # y = mx + b
    cumulative_spend = float(cumulative_spend)
    probabilities = {}

    racecar_prob = max( (float(-1 * slope_racecar) * cumulative_spend) + float( racecar_intercept), 0)

    if cumulative_spend <= doll_peak:
        doll_prob = max( float(slope_doll) * cumulative_spend, 0 )
    else:
        doll_prob = max( (-1 * float(slope_doll) * cumulative_spend) + float( doll_intercept ), 0)

    teddy_bear_prob = 1 - (racecar_prob + doll_prob)

    probabilities['Racecar'] = racecar_prob
    probabilities['Doll'] = doll_prob
    probabilities['TeddyBear'] = teddy_bear_prob


    # this section deals with the logic if one or more toys have already been unlocked
    lost_prob = 0
    enabled_count = 0
    for toy in toys:
      if toy.enabled:
          lost_prob += probabilities[toy.name]
          probabilities[toy.name] = 0
          enabled_count += 1
    added_prob = lost_prob / (3 - enabled_count)

    for toy in toys:
        if not toy.enabled:
            probabilities[toy.name] += added_prob

    return probabilities


def pick_unlocked_toy(toy_probabilities):
    toys = list( toy_probabilities.keys() )
    weights = list( toy_probabilities.values() )
    selection = random.choices(toys, weights=weights, k=1)
    return selection