from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse


class Toy_Basket(models.Model):
    name = models.CharField(max_length=100, default="basket")

    def __str__(self):
        return self.name


class Toy(models.Model):
    name = models.CharField(max_length=50)
    price_per_unit = models.DecimalField(max_digits=10, decimal_places=2)
    cost_per_unit = models.DecimalField(max_digits=10, decimal_places=2)
    demand_distribution_json = models.JSONField(
        default=list,  # e.g., [0.05, 0.10, 0.15, ..., 0.05] 20 values
        help_text="Discrete probability distribution for demand (6 steps)"
    )
    toy_basket = models.ForeignKey(Toy_Basket, on_delete=models.CASCADE, null=True, blank=True, related_name="toys")
    enabled = models.BooleanField(null=True)

    def adjusted_cost(self, coefficient):
        return self.cost_per_unit * coefficient

    def __str__(self):
        return self.name

class InsuranceEvent(models.Model):
    name = models.CharField(max_length=50)
    premium_cost = models.DecimalField(max_digits=10, decimal_places=2)
    disaster_cost = models.DecimalField(max_digits=10, decimal_places=2)
    demand_distribution_json = models.JSONField(
        default=list,  # e.g., [0.05, 0.10, 0.15, ..., 0.05] 20 values
        help_text="cost of insurance disaster (6 sided dice)"
    )

    def __str__(self):
        return self.name


class InsuranceEventOutcome(models.Model):
    turn = models.ForeignKey(
        "Turn",
        on_delete=models.CASCADE,
        related_name="insurance_decisions"
    )
    insurance_event = models.ForeignKey(InsuranceEvent, on_delete=models.CASCADE)
    dice_roll = models.IntegerField()
    disaster_cost_realized = models.DecimalField(max_digits=10, decimal_places=2)
    coverage_active = models.BooleanField(default=False)
    premium_cost = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.insurance_event.name


class Difficulty(models.Model):
    DIFFICULTY_CHOICES = [
        ("easy", "Easy"),
        ("medium", "Medium"),
        ("hard", "Hard"),
    ]

    name = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES, unique=True)

    # Game rule variables
    starting_cash = models.DecimalField(max_digits=12, decimal_places=2)
    max_turns = models.IntegerField(default=20)
    starting_factory_space = models.IntegerField(default=150)
    factory_space_cost_coefficient = models.DecimalField(max_digits=12, decimal_places=2, null=True)
    winning_networth = models.DecimalField(max_digits=12, decimal_places=2)
    rent_cost = models.DecimalField(max_digits=12, decimal_places=2)
    tax_rate = models.DecimalField(max_digits=12, decimal_places=2)

    new_product_success_cost_coefficient = models.DecimalField(max_digits=12, decimal_places=6, null=True)
    new_product_success_b = models.DecimalField(max_digits=12, decimal_places=2, null=True)


    # new toy unlocking inputs
    slope_racecar = models.DecimalField(max_digits=12, decimal_places=6, null=True)
    intercept_racecar = models.DecimalField(max_digits=12, decimal_places=6, null=True)
    slope_doll = models.DecimalField(max_digits=12, decimal_places=6, null=True)
    intercept_doll = models.DecimalField(max_digits=12, decimal_places=6, null=True)
    peak_doll = models.DecimalField(max_digits=12, decimal_places=6, null=True)


    #financing related
    min_loan_amount = models.DecimalField(max_digits=12, decimal_places=2, default=100)
    min_years_of_financial_history = models.IntegerField(default=3)

    insurance_enabled = models.BooleanField(default=True)
    financing_enabled = models.BooleanField(default=True)
    ads_enabled = models.BooleanField(default=True)
    equipment_enabled = models.BooleanField(default=True)
    rnd_enabled = models.BooleanField(default=True)


    def __str__(self):
        return self.get_name_display()


class Player(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    difficulty = models.ForeignKey(
        Difficulty,
        on_delete=models.PROTECT,
        null=True,  # add this
        blank=True
    )

    name = models.CharField(max_length=100)
    company_name = models.CharField(max_length=100, default="None")
    age = models.IntegerField(default=20)
    turn_number = models.IntegerField(default=1)

    cash = models.DecimalField(max_digits=12, decimal_places=0, default=0)
    total_equity = models.DecimalField(max_digits=12, decimal_places=0, default=0)
    factory_space = models.IntegerField(default=150)

    status = models.CharField(default="still_playing", null=True,blank=True)
    lost_reason = models.CharField(default="None", null=True, blank=True)

    is_active = models.BooleanField(default=True)
    cost_savings_coefficient = models.DecimalField(max_digits=12, decimal_places=2, default=1)
    equipment_bought = models.BooleanField(default=False)
    equipment_name = models.CharField(max_length=100, default="None")
    depreciation_expense_ends_turn = models.IntegerField(default=0)
    depreciation_expense_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    next_offered_rate = models.DecimalField(max_digits=6, decimal_places=4, default=0.10)

    cumulative_rnd_spend = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    toy_unlocked = models.BooleanField(default=False)
    unlocked_toy_name = models.CharField(max_length=100, default="None")


    def __str__(self):
        return self.name


class Equipment(models.Model):
    name = models.CharField(max_length=50)
    cost_savings_percent = models.DecimalField(max_digits=10, decimal_places=2)
    cost = models.DecimalField(max_digits=10, decimal_places=2)
    useful_life = models.IntegerField(default=0)

    def __str__(self):
        return self.name


class ToyProductionOutcome(models.Model):
    turn = models.ForeignKey(
        "Turn",
        on_delete=models.CASCADE,
        related_name="production_decisions"
    )
    toy = models.ForeignKey(Toy, on_delete=models.CASCADE)
    roll = models.IntegerField()
    demand_percent = models.IntegerField()

    units_manufactured = models.IntegerField()
    units_sold = models.IntegerField(default=0)

    revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    cogs = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    profit = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    demand_boost_applied = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    def baseline_units_sold(self):
        """Units that would have sold with no ad boost applied this turn."""
        baseline = round(self.units_manufactured * (self.demand_percent / 100))
        return min(baseline, self.units_sold)

    def boosted_units_sold(self):
        """Portion of units_sold attributable to an active ad boost."""
        return self.units_sold - self.baseline_units_sold()

    def __str__(self):
        return self.name



class Turn(models.Model):
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    turn_number = models.IntegerField()

    # income_statement
    revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    Cost_of_Goods_Sold = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    gross_profit = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    operating_expenses = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    EBITDA = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    taxes = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    depreciation = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    interest_expense = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    EBT = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    other_costs = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    net_income = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    ad_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    disaster_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    premium_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    rnd_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)


    # cash flow statement
    free_cash_flow = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    interest_tax_shield = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    operating_cf = models.DecimalField(max_digits=12, decimal_places=2, default=0)


    #CFI
    expansion_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    equipment_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_capex = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    investing_cf = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    # CFF
    principal_payment = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    loan_proceeds = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    financing_cf = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    change_in_cash = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    beginning_cash = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    ending_cash = models.DecimalField(max_digits=12, decimal_places=2, default=0)


    # balance sheet
    #assets
    cash = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    # eventually - add inventory
    gross_equipment = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    accumulated_depreciation_equipment = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    property = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    gross_ppe = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    total_assets = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    #liabilities
    loans_payable = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    #shareholders equity
    retained_earnings = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    # eventually will add in equity investors
    total_equity = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    # new product success inputs
    new_product_produced = models.BooleanField(default=False)
    new_product_roll = models.IntegerField(null=True, blank=True)
    new_product_threshold = models.IntegerField(null=True, blank=True)



    def __str__(self):
        return f"Turn {self.turn_number} - {self.player.name}"


class Game(models.Model):
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    toy_basket = models.ForeignKey(Toy_Basket, on_delete=models.CASCADE, null=True, blank=True)

class AdvertisingProfile(models.Model):
    difficulty = models.ForeignKey(Difficulty, on_delete=models.CASCADE, related_name='advertising_profiles')
    boost_schedule = models.JSONField(
        default=list,
        help_text="Demand boost multipliers by turn offset. e.g. [1.0, 0.5, 0.25] means "
                  "100% boost turn 1, 50% turn 2, 25% turn 3, then zero."
    )
    cost = models.DecimalField(max_digits=12, decimal_places=2)
    name = models.CharField(max_length=100, default="Advertising Campaign")

    def __str__(self):
        return self.name

class AdvertisingCampaign(models.Model):
    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='campaigns')
    profile = models.ForeignKey(AdvertisingProfile, on_delete=models.PROTECT)
    purchased_on_turn = models.IntegerField()

    def boost_for_turn(self, current_turn):
        offset = current_turn - self.purchased_on_turn - 1
        schedule = self.profile.boost_schedule
        if 0 <= offset < len(schedule):
            return schedule[offset]
        return 0.0

    def __str__(self):
        return f"Campaign for {self.player} (turn {self.purchased_on_turn})"


class PlayerLoan(models.Model):
    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='loans')
    taken_on_turn = models.IntegerField()

    # Locked-in terms
    principal = models.DecimalField(max_digits=12, decimal_places=2)
    annual_interest_rate = models.DecimalField(max_digits=6, decimal_places=4)
    loan_length = models.IntegerField()  # in turns
    annual_payment = models.DecimalField(max_digits=12, decimal_places=2)

    # Running balance
    outstanding_balance = models.DecimalField(max_digits=12, decimal_places=2)
    is_paid_off = models.BooleanField(default=False)

    def compute_annual_payment(self):
        r = self.annual_interest_rate
        n = self.loan_length
        P = self.principal
        return P * r * (1 + r) ** n / ((1 + r) ** n - 1)

    def interest_due(self):
        return self.outstanding_balance * self.annual_interest_rate

    def principal_due(self):
        return self.annual_payment - self.interest_due()



class InterestRateProfile(models.Model):
    difficulty = models.ForeignKey(Difficulty, on_delete=models.CASCADE, related_name='rate_profiles')
    name = models.CharField(max_length=100, default="Standard Rate")
    rate_distribution_json = models.JSONField(
        default=list,
        help_text="List of [rate, weight] pairs. e.g. [[0.07, 20], [0.10, 50], [0.13, 30]]"
    )

    def __str__(self):
        return self.name


class Post(models.Model):
    title = models.CharField(max_length=100)
    content = models.TextField()
    date_posted = models.DateTimeField(auto_now_add=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.title


    def get_absolute_url(self):
        return reverse("post-detail", kwargs={"pk": self.pk})