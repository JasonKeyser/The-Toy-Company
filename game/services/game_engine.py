from decimal import Decimal
from django.db import transaction
from django.utils.text import normalize_newlines

from .distributions import pick_from_distribution, pick_from_disaster_distribution
from game.models import Turn, ToyProductionOutcome, Player, InsuranceEventOutcome


def check_player_status(player):
    if player.total_equity >= player.difficulty.winning_networth:
        player.status = "won"
    elif player.cash <= 0:
        player.status = "lost"
        player.lost_reason = "went bankrupt"
    elif player.turn_number > player.difficulty.max_turns:
        player.status = "lost"
        player.lost_reason = "lost on turns"

    else:
        player.status = "still_playing"
    player.save()


def get_total_boost(player, current_turn):
    active = player.campaigns.all()
    total = sum(c.boost_for_turn(current_turn) for c in active)
    return total



class GameEngine:
    @transaction.atomic
    def process_turn(self, player, toy_production_choices, insurance_choices, ad_cost, capex_choices, cost_savings_coefficient, borrowed_amount):

        total_revenue = Decimal("0.00")
        total_cogs = Decimal("0.00")

        # 1️⃣ Create Turn FIRST
        last_turn = Turn.objects.filter(player=player).order_by("-turn_number").first()
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
            loan.outstanding_balance = round(loan.outstanding_balance - loan.principal_due(), 2)
            if abs(loan.outstanding_balance) < 1:
                loan.is_paid_off = True
            loan.save()


        # income statement inputs
        EBT = EBITDA - round(depreciation + interest_expense,2)
        tax_expense = max( round( EBT * player.difficulty.tax_rate, 2), 0)
        other_costs = round(tax_expense + depreciation + interest_expense, 2)
        total_cost = round( total_cogs + operating_expenses + other_costs, 2)
        net_income = round( total_revenue - total_cost, 2)

        #capex inputs
        expansion_cost = capex_choices['expansion_cost']
        equipment_cost = capex_choices['equipment_cost']
        total_capex = round(expansion_cost + equipment_cost, 2)

        # financing inputs
        loan_proceeds = borrowed_amount
        principal_paid = principal_payment

        # ── Cash Flow Statement ───────────────────────
        operating_cf = round(net_income + depreciation, 2)
        investing_cf = -total_capex
        financing_cf = round(loan_proceeds - principal_paid, 2)
        change_in_cash = round(operating_cf + investing_cf + financing_cf, 2)
        interest_tax_shield = ( round(interest_expense * (1 - player.difficulty.tax_rate),  2))
        free_cash_flow = round(net_income - total_capex + depreciation, 2) + interest_tax_shield
        # THERE IS A DIFFERENCE BETWEEN FREE CASH FLOW AND CHANGE IN CASH
            # Free Cashflow is a metric used to measure profitability and ultimately drives business value
            # Change in cash includes cash flow from financing which is not indicative of business performance but shows the actual change in cash

        # ── Balance Sheet ─────────────────────────────

        # Prior balance sheet values — zero on turn 1
        prior_gross_equipment = last_turn.gross_equipment if last_turn else Decimal("0")
        prior_accumulated_depreciation = last_turn.accumulated_depreciation_equipment if last_turn else Decimal("0")
        prior_property = last_turn.property if last_turn else Decimal("0")
        prior_loans_payable = last_turn.loans_payable if last_turn else Decimal("0")
        starting_retained_earnings = player.difficulty.starting_cash
        prior_retained_earnings = last_turn.retained_earnings if last_turn else starting_retained_earnings #keeps accounting equation in balance for turn 0



        ending_cash = round(player.cash + change_in_cash, 2)
        gross_equipment = round(prior_gross_equipment + equipment_cost, 2)
        accumulated_depreciation_equipment = round(prior_accumulated_depreciation + depreciation, 2)
        net_equipment = round(gross_equipment - accumulated_depreciation_equipment, 2)
        property = round(prior_property + expansion_cost, 2)
        gross_ppe = round(net_equipment + property, 2)
        loans_payable = round(prior_loans_payable - principal_paid + loan_proceeds, 2)
        retained_earnings = round(prior_retained_earnings + net_income, 2)


        total_assets = ending_cash + gross_ppe
        total_liabilities = loans_payable
        total_equity = retained_earnings

        # ── Integrity checks ──────────────────────────
        if ( round(total_assets, 0) - round(total_liabilities + total_equity, 0) ) > 1:
            raise ValueError(
                f"Balance sheet doesn't balance: "
                f"assets={total_assets}, L+E={total_liabilities + total_equity}"
            )


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
        turn.interest_tax_shield = interest_tax_shield

        turn.free_cash_flow = free_cash_flow

        #CFO
        turn.operating_cf = operating_cf

        #CFI
        turn.expansion_cost = expansion_cost
        turn.equipment_cost = equipment_cost
        turn.total_capex = total_capex
        turn.investing_cf = investing_cf

        #CFF
        turn.principal_payment = principal_payment
        turn.loan_proceeds = loan_proceeds
        turn.financing_cf = financing_cf

        # Balance Sheet

        #assets
        turn.beginning_cash = player.cash
        turn.ending_cash = player.cash + change_in_cash
        turn.change_in_cash = change_in_cash
        turn.gross_equipment = gross_equipment
        turn.accumulated_depreciation_equipment = accumulated_depreciation_equipment
        turn.property = property
        turn.gross_ppe = gross_ppe
        turn.total_assets = total_assets

        #liabilities
        turn.loans_payable = loans_payable

        #equity
        turn.retained_earnings = retained_earnings
        turn.total_equity = total_equity

        turn.save()

        # 5️⃣ Update player AFTER Turn is saved
        player.cash += change_in_cash
        player.total_equity = total_equity
        player.cost_savings_coefficient = cost_savings_coefficient
        player.turn_number += 1


        #check here to see if the player won or lost
        check_player_status(player)

        rate_profile = player.difficulty.rate_profiles.first()
        if rate_profile:
            from .distributions import pick_interest_rate
            player.next_offered_rate = pick_interest_rate(rate_profile)
        player.save()


        return turn

