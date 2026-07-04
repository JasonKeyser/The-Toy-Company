import random

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


def calculate_product_chances(cumulative_spend, slope_racecar, racecar_intercept, slope_doll, doll_peak, doll_intercept):
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



    return probabilities


def pick_unlocked_toy(toy_probabilities):
    toys = list( toy_probabilities.keys() )
    weights = list( toy_probabilities.values() )
    selection = random.choices(toys, weights=weights, k=1)
    return selection