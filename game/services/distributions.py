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