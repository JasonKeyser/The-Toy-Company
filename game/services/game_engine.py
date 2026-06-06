from decimal import Decimal
from django.db import transaction
from django.utils.text import normalize_newlines

from .distributions import pick_from_distribution, pick_from_disaster_distribution
from game.models import Turn, ToyProductionOutcome, Player, InsuranceEventOutcome


def check_player_status(player):
    if player.cash >= player.difficulty.winning_cash:
        player.status = "won"
    elif player.cash <= 0:
        player.status = "lost"
        player.lost_reason = "ran_out_of_money"
    elif player.turn_number > player.difficulty.max_turns:
        player.status = "lost"
        player.lost_reason = "lost_on_turns"

    else:
        player.status = "still_playing"
    player.save()


def get_total_boost(player, current_turn):
    active = player.campaigns.all()
    total = sum(c.boost_for_turn(current_turn) for c in active)
    return total



class GameEngine:
    @transaction.atomic
    def process_turn(self, player, toy_production_choices, insurance_choices, ad_cost, capex_choices, cost_savings_coefficient):

        total_revenue = Decimal("0.00")
        total_cogs = Decimal("0.00")

        # 1️⃣ Create Turn FIRST
        turn = Turn.objects.create(
            player=player,
            turn_number=player.turn_number
        )

        # 2️⃣ Process each toy
        for toy, units_manufactured in toy_production_choices.items():

            boost = get_total_boost(player, player.turn_number)
            roll, fraction = pick_from_distribution(toy)
            boosted_fraction = min(1.0, fraction * (1 + boost))

            units_sold = int( round( units_manufactured * boosted_fraction, 0) )

            revenue = units_sold * toy.price_per_unit
            cogs = units_manufactured * toy.adjusted_cost(player.cost_savings_coefficient)
            gross_profit = revenue - cogs


            total_revenue += revenue
            total_cogs += cogs

            # 3️⃣ Save ProductionDecision to DB
            ToyProductionOutcome.objects.create(
                turn=turn,
                toy=toy,
                roll=roll,
                demand_percent=round(fraction * 100),
                units_manufactured=units_manufactured,
                units_sold=units_sold,
                revenue=revenue,
                cogs=cogs,
                profit=gross_profit,
                demand_boost_applied=boost,
            )

        total_premium_cost = 0
        total_disaster_cost_realized = 0
        for insurance_event, coverage_taken in insurance_choices.items():

            if coverage_taken:
                disaster_cost_realized = 0
                insurance_dice_roll = 0
                premium_cost = insurance_event.premium_cost
            else:
                insurance_dice_roll, disaster_cost_realized = pick_from_disaster_distribution(insurance_event)
                premium_cost = 0

            total_premium_cost += premium_cost
            total_disaster_cost_realized += disaster_cost_realized
            # Save to DB
            InsuranceEventOutcome.objects.create(
                turn=turn,
                insurance_event=insurance_event,
                dice_roll = insurance_dice_roll,
                disaster_cost_realized = disaster_cost_realized,
                coverage_active = coverage_taken,
                premium_cost = premium_cost
            )



        total_gross_profit = total_revenue - total_cogs
        operating_expenses = player.difficulty.rent_cost + ad_cost + total_disaster_cost_realized + total_premium_cost
        EBITDA = total_gross_profit - operating_expenses

        if player.turn_number < player.depreciation_expense_ends_turn:
            depreciation = player.depreciation_expense_amount
        else:
            depreciation = 0

        active_loans = player.loans.filter(is_paid_off=False)
        interest_expense = 0
        principal_payment = 0
        for loan in active_loans:
            interest_expense += loan.interest_due()
            principal_payment += loan.principal_due()
            loan.outstanding_balance -= loan.annual_payment()
            if loan.outstanding_balance == 0:
                loan.is_paid_off = True
            loan.save()


        EBT = EBITDA - depreciation - interest_expense
        tax_expense = max( EBT * player.difficulty.tax_rate, 0)
        other_costs = tax_expense + depreciation
        total_cost = total_cogs + operating_expenses + other_costs
        net_income = total_revenue - total_cost
        expansion_cost = capex_choices['expansion_cost']
        equipment_cost = capex_choices['equipment_cost']
        total_capex = expansion_cost + equipment_cost


        # 4️⃣ Save financial summary on Turn
        turn.revenue = total_revenue
        turn.Cost_of_Goods_Sold = total_cogs
        turn.gross_profit = total_gross_profit
        turn.operating_expenses = operating_expenses
        turn.EBITDA = EBITDA
        turn.depreciation = depreciation
        turn.interest_expense = interest_expense
        turn.taxes = tax_expense
        turn.other_costs = other_costs
        turn.total_cost = total_cost
        turn.net_income = net_income

        turn.ad_cost = ad_cost
        turn.disaster_cost = total_disaster_cost_realized
        turn.premium_cost = total_premium_cost
        turn.expansion_cost = expansion_cost
        turn.equipment_cost = equipment_cost
        turn.total_capex = total_capex


        turn.principal_payment = principal_payment
        turn.free_cash_flow = net_income - total_capex + depreciation - principal_payment

        turn.beginning_cash = player.cash #remove any borrowed funds?
        turn.ending_cash = player.cash + turn.free_cash_flow
        turn.save()

        # 5️⃣ Update player AFTER Turn is saved
        player.cash += net_income
        player.cost_savings_coefficient = cost_savings_coefficient
        player.turn_number += 1


        #check here to see if the player won or lost
        check_player_status(player)

        return turn

