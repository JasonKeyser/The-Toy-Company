from django.contrib.admin.helpers import AdminForm
from django.shortcuts import render, get_object_or_404, redirect
import datetime
from django.contrib.auth.models import User
from .models import Post, Toy, Player, Turn, ToyProductionOutcome, Difficulty, Game, AdvertisingProfile, \
    AdvertisingCampaign, InsuranceEvent, Equipment, InsuranceEventOutcome, PlayerLoan, InterestRateProfile
from .services.game_engine import GameEngine
from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    DeleteView)
from django.contrib.auth.decorators import login_required

class PostListView(ListView):
    model = Post

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from .forms import UnitsManufacturedForm, BaseUnitsFormSet, FactoryExpansionForm, AdvertisementCampaignForm, \
    InsuranceCoverageTakenForm, BaseCoverageFormSet, EquipmentForm, LoanForm
from django.forms import formset_factory
from django.forms.utils import ErrorList
from django.contrib import messages
from .services.distributions import pick_interest_rate

class PostListView(ListView):
    model = Post
    template_name = 'game/home.html'
    context_object_name = 'posts'
    ordering = ['-date_posted']
    paginate_by = 5


class UserPostListView(ListView):
    model = Post
    template_name = 'game/user_posts.html'
    context_object_name = 'posts'
    paginate_by = 5

    def get_queryset(self):
        user = get_object_or_404(User, username=self.kwargs.get('username'))
        return Post.objects.filter(author=user).order_by('-date_posted')



class PostDetailView(DetailView):
    model = Post

class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    fields = ['title', 'content']

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

class PostUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Post
    fields = ['title', 'content']

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def test_func(self):
        post = self.get_object()
        if self.request.user == post.author:
            return True
        return False


class PostDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Post
    success_url = '/'

    def test_func(self):
        post = self.get_object()
        if self.request.user == post.author:
            return True
        return False



def about(request):
    context = {
        'title' : "About",
    }
    return render(request, 'game/about.html', context)

@login_required
def game_begin(request):
    user = request.user
    if request.method == "POST":
        difficulty_value = request.POST.get("difficulty")
        difficulty_obj = Difficulty.objects.get(name=difficulty_value)
        company_name = request.POST.get("factory_name")

        player = Player.objects.create(
            user=user,
            difficulty=difficulty_obj,
            name=user.username,
            cash=difficulty_obj.starting_cash,
            total_equity = difficulty_obj.starting_cash, # no liabilities or other assets at game begin so need this for it BS to balance
            factory_space = difficulty_obj.starting_factory_space,
            company_name = company_name
        )

        game = Game.objects.create(
            player=player
        )

        return redirect("game-production")

    return render(request, "game/game_begin.html")



def game(request):
    game = Game.objects.last()
    player = game.player

    toys = Toy.objects.all()

    UnitsFormSet = formset_factory(
        UnitsManufacturedForm,
        formset=BaseUnitsFormSet,
        extra = len(toys)
        )

    insurance_events = InsuranceEvent.objects.all()
    CoverageFormSet = formset_factory(
        InsuranceCoverageTakenForm,
        formset=BaseCoverageFormSet,
        extra = len(insurance_events),
        )

    current_turn = player.turn_number
    active_campaigns = player.campaigns.all()
    current_boost = sum(c.boost_for_turn(current_turn) for c in active_campaigns)

    # upcoming boosts for the next N turns (for the widget)
    upcoming_boosts = []
    for offset in range(1, 4):
        future_turn = current_turn + offset
        boost = sum(c.boost_for_turn(future_turn) for c in active_campaigns)
        upcoming_boosts.append((future_turn, round(boost * 100)))

    # available ad profiles for this difficulty
    available_ad_profiles = AdvertisingProfile.objects.filter(difficulty=player.difficulty)


    equipment = Equipment.objects.all()
    notifications = []

    max_leverage_ratio = 10

    minimum_credit_available = player.difficulty.min_loan_amount
    min_years_of_financial_history = player.difficulty.min_years_of_financial_history
    min_yrs_met = player.turn_number > min_years_of_financial_history

    if min_yrs_met:
        last_three_turns = Turn.objects.filter(player=player).order_by("-turn_number")[:3]
        ebitdas = []
        for turn in last_three_turns:
            ebitdas.append(turn.EBITDA)

        trailing_ebitda = sum(ebitdas) / len(ebitdas)
    else:
        trailing_ebitda = 0



    active_loans = player.loans.filter(is_paid_off=False)
    if active_loans.count() > 0:
        current_loan_outstanding = True
    else:
        current_loan_outstanding = False

    eligable = (min_yrs_met == True) and (current_loan_outstanding == False)

    if eligable:
        max_credit = max( trailing_ebitda * max_leverage_ratio, minimum_credit_available )
    else:
        max_credit = "N/A"

    rolled_rate = player.next_offered_rate
    loan_offer = {
        "interest_rate": rolled_rate,
        "loan_length": 10,
        "max_leverage_ratio": max_leverage_ratio,
        "trailing_ebitda": trailing_ebitda,
        "min_credit" : minimum_credit_available,
        "max_credit": max_credit,
        "eligible": eligable,
        "min_yrs_met": min_yrs_met,
        "current_loan_outstanding": current_loan_outstanding,
    }

    if request.method == "POST":
        toyformset = UnitsFormSet(request.POST, factory_space=player.factory_space, prefix="toys")
        coverageformset = CoverageFormSet(request.POST, prefix="coverage")
        inv_expansion_form = FactoryExpansionForm(request.POST)
        loan_form = LoanForm(request.POST)
        ad_form = AdvertisementCampaignForm(request.POST, difficulty=player.difficulty)
        equipment_form = EquipmentForm(request.POST, equipment_bought=player.equipment_bought)

        if toyformset.is_valid() and inv_expansion_form.is_valid() and ad_form.is_valid() and coverageformset.is_valid() and equipment_form.is_valid()\
                and loan_form.is_valid():

            difficulty = player.difficulty

            if difficulty.ads_enabled:
                selected_ad_profile = ad_form.cleaned_data.get("ad_campaign")
                ad_cost = selected_ad_profile.cost if selected_ad_profile else 0
            else:
                selected_ad_profile = None
                ad_cost = 0

            if difficulty.equipment_enabled:
                selected_equipment = equipment_form.cleaned_data.get("equipment")
            else:
                selected_equipment = None

            if selected_equipment:
                equipment_cost = selected_equipment.cost
                player.equipment_bought = True
                player.equipment_name = selected_equipment.name
                cost_savings_coefficient = selected_equipment.cost_savings_percent
                player.depreciation_expense_ends_turn = player.turn_number + selected_equipment.useful_life
                player.depreciation_expense_amount = equipment_cost / selected_equipment.useful_life
            else:
                equipment_cost = 0
                cost_savings_coefficient = player.cost_savings_coefficient



            toy_production_choices = {}
            toy_cost = 0

            for tform, toy in zip(toyformset, toys):
                units = tform.cleaned_data.get("units_to_manufacture", 0)
                toy_cost += toy.adjusted_cost(player.cost_savings_coefficient) * units
                toy_production_choices[toy] = units

            insurance_coverage_choices = {}
            premium_cost = 0

            if difficulty.insurance_enabled:
                for iform, insurance_event in zip(coverageformset, insurance_events):
                    coverage_taken = iform.cleaned_data.get("coverage_taken", 0)
                    if coverage_taken:
                        premium_cost += insurance_event.premium_cost
                    insurance_coverage_choices[insurance_event] = coverage_taken

            extra_space = inv_expansion_form.cleaned_data.get("extra_space", 0)
            expansion_cost = extra_space * player.difficulty.factory_space_cost


            if difficulty.financing_enabled:
                borrowed_amount = loan_form.cleaned_data.get("borrowed_amount", 0)
            else:
                borrowed_amount = 0

            rent = player.difficulty.rent_cost
            cogs = toy_cost
            opex = rent + ad_cost + premium_cost
            capex = expansion_cost + equipment_cost

            total_proposed_spend = cogs + opex + capex
            if total_proposed_spend > (player.cash + borrowed_amount):
                toyformset._non_form_errors = toyformset.error_class([
                    f"Insufficent Funds! Total planned expenditure is ${round(total_proposed_spend, 0)}, but you only have ${round(player.cash + borrowed_amount,0)}."
                ])
            else:

                player.factory_space += extra_space
                player.save()


                if borrowed_amount > 0:
                    loan = PlayerLoan(
                        player=player,
                        taken_on_turn=player.turn_number,
                        annual_interest_rate= loan_offer["interest_rate"],
                        loan_length= loan_offer["loan_length"],
                        principal= borrowed_amount,
                        outstanding_balance= borrowed_amount,
                    )
                    loan.annual_payment = loan.compute_annual_payment()
                    loan.save()


                if selected_ad_profile and difficulty.ads_enabled:
                    AdvertisingCampaign.objects.create(
                        player=player,
                        profile=selected_ad_profile,
                        purchased_on_turn=player.turn_number
                    )

                capex_choices = {
                    'expansion_cost': expansion_cost,
                    'equipment_cost': equipment_cost,
                }

                engine = GameEngine()
                turn = engine.process_turn(player, toy_production_choices, insurance_coverage_choices, ad_cost, capex_choices, cost_savings_coefficient, borrowed_amount)
                return render(request, "game/dice_roll.html", {"turn": turn})

    elif request.method == "GET":
        #Alerts for new items
        last_turn = Turn.objects.filter(player=player).order_by("-turn_number").first()

        if last_turn and last_turn.expansion_cost > 0:
            notifications.append(f"🏭 Factory Space increased to {player.factory_space}!")

        if last_turn and last_turn.equipment_cost > 0:
            savings_pct = round((1 - float(player.cost_savings_coefficient)) * 100)
            notifications.append(
                f"⚙️ {player.equipment_name} now installed! "
                f"Cost per unit on all toys is reduced by {savings_pct}%."
            )
        if player.turn_number == min_years_of_financial_history + 1 and player.difficulty.financing_enabled:
            notifications.append(
                f"💵 {player.company_name} now eligible for debt financing! "
            )
        toyformset = UnitsFormSet(factory_space=player.factory_space, prefix="toys")
        coverageformset = CoverageFormSet(prefix="coverage")
        inv_expansion_form = FactoryExpansionForm()
        loan_form = LoanForm()
        ad_form = AdvertisementCampaignForm(difficulty=player.difficulty)
        equipment_form = EquipmentForm(equipment_bought=player.equipment_bought)


    print(f'savings {player.cost_savings_coefficient}')
    form_and_toys = [
        (form, toy, toy.adjusted_cost(player.cost_savings_coefficient))
        for form, toy in zip(toyformset, toys)
    ]
    ad_profiles_json = {
        str(p.id): {
            "cost": float(p.cost),
            "boost_schedule": p.boost_schedule,
            "name": p.name,
        }
        for p in available_ad_profiles
    }

    equipment_json = {
        str(e.id): {
            "cost": float(e.cost),
            "cost_savings_percent": float(e.cost_savings_percent),
            "name": e.name,
        }
        for e in equipment
    }

    return render(request, "game/production.html", {
            "player": player,
            "current_boost":current_boost,
            "toyformset": toyformset,
            "form_and_toys": form_and_toys,
            "coverageformset": coverageformset,
            "insurance_events": insurance_events,
            "inv_expansion_form": inv_expansion_form,
            "loan_offer": loan_offer,
            "loan_form": loan_form,
            "ad_form": ad_form,
            "available_ad_profiles": available_ad_profiles,
            "current_boost": round(current_boost * 100),
            "upcoming_boosts": upcoming_boosts,
            "ad_profiles_json": ad_profiles_json,
            "equipment_form": equipment_form,
            "equipment_json": equipment_json,
            'notifications': notifications,

        })


def turn_summary(request):
    game = Game.objects.last()
    player = game.player
    turn = Turn.objects.filter(player=player).order_by("-turn_number").first()
    production_outcomes = ToyProductionOutcome.objects.filter(turn=turn)
    beginning_cash = turn.player.cash - turn.free_cash_flow

    if not turn:
        return redirect("game")

    # if the player won or lost - bring them to a new screen
    if player.status == "still_playing":
        return render(request, "game/turn_summary.html", {
            "turn": turn,
            "production_outcomes": production_outcomes,
            "beginning_cash": beginning_cash,
        })

    else:
        return render(request, "game/game_over.html", {"player" : player})


def financial_history(request):
    game = Game.objects.last()
    player = game.player
    turns = Turn.objects.filter(player=player)
    turn = turns.order_by("-turn_number").first()
    production_outcomes = ToyProductionOutcome.objects.filter(turn=turn)
    insurance_events = InsuranceEvent.objects.all()

    return render(request, "game/financial_history.html", {
        "turns": turns,
        "turn": turn,
        "production_outcomes": production_outcomes,
        "insurance_events": insurance_events,
    })


@login_required
def demand_distribution_view(request):
    toys = Toy.objects.all()
    toy_distributions = []
    for toy in toys:
        # Use the toy's stored distribution
        dist = toy.demand_distribution_json
        # Convert to percentages for display
        percentages = [p*100 for p in dist]
        toy_distributions.append({
            "toy": toy,
            "percentages": percentages
        })

    percentage_range = range(1, len(dist) + 1)
    context = {
        "toy_distributions": toy_distributions,
        "percentage_range": percentage_range,
    }

    return render(request, "game/demand_distribution.html", context)



@login_required
def insurance_distribution_view(request):
    insurance_events = InsuranceEvent.objects.all()
    insurance_distributions = []
    for insurance_event in insurance_events:
        dist = insurance_event.demand_distribution_json
        # Convert to percentages for display
        disaster_costs = [c for c in dist]
        insurance_distributions.append({
            "insurance_event": insurance_event,
            "disaster_costs": disaster_costs
        })

    cost_range = range(1, len(dist) + 1)
    context = {
        "insurance_distributions": insurance_distributions,
        "cost_range": cost_range,
    }

    return render(request, "game/insurance_distribution.html", context)



@login_required
def interest_rate_distribution_view(request):
    game = Game.objects.last()
    player = game.player
    rate_profiles = InterestRateProfile.objects.filter(difficulty=player.difficulty)

    context = {
        "rate_profiles": rate_profiles,
    }
    return render(request, "game/interest_rate_distribution.html", context)