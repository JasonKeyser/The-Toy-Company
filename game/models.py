from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse


class Toy(models.Model):
    name = models.CharField(max_length=50)
    price_per_unit = models.DecimalField(max_digits=10, decimal_places=2)
    cost_per_unit = models.DecimalField(max_digits=10, decimal_places=2)
    demand_distribution_json = models.JSONField(
        default=list,  # e.g., [0.05, 0.10, 0.15, ..., 0.05] 20 values
        help_text="Discrete probability distribution for demand (6 steps)"
    )

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
    factory_space_cost = models.DecimalField(max_digits=12, decimal_places=2, null=True)
    winning_cash = models.DecimalField(max_digits=12, decimal_places=2)
    rent_cost = models.DecimalField(max_digits=12, decimal_places=2)
    tax_rate = models.DecimalField(max_digits=12, decimal_places=2)

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

    cash = models.DecimalField(max_digits=12, decimal_places=0)
    factory_space = models.IntegerField(default=150)

    status = models.CharField(default="still_playing", null=True,blank=True)
    lost_reason = models.CharField(default="None", null=True, blank=True)

    is_active = models.BooleanField(default=True)
    cost_savings_coefficient = models.DecimalField(max_digits=12, decimal_places=2, default=1)
    equipment_bought = models.BooleanField(default=False)
    equipment_name = models.CharField(max_length=100, default="None")
    depreciation_expense_ends_turn = models.IntegerField(default=0)
    depreciation_expense_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)

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

    def __str__(self):
        return self.name



class Turn(models.Model):
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    turn_number = models.IntegerField()

    revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    Cost_of_Goods_Sold = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    gross_profit = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    operating_expenses = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    EBITDA = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    taxes = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    depreciation = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    EBT = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    other_costs = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    net_income = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    ad_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    disaster_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    premium_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    expansion_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    equipment_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_capex = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    free_cash_flow = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    beginning_cash = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    ending_cash = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Turn {self.turn_number} - {self.player.name}"


class Game(models.Model):
    player = models.ForeignKey(Player, on_delete=models.CASCADE)


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


class Loan(models.Model):
    player = models.ForeignKey(Player, on_delete=models.CASCADE) #add a related name?

    #term sheet
    interest_rate = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    loan_length = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    max_leverage_ratio = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    max_amount_available_to_borrow = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    minimum_available_credit = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    #what happened this turn
    player_able_to_borrow = models.BooleanField(default=False)
    money_borrowed_this_turn = models.BooleanField(default=False)
    money_borrowed_on_turn = models.IntegerField(default=0)
    amount_borrowed = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    #amortization schedule
    balance_begin_turn = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    balance_end_turn = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    loan_year = models.IntegerField(default=0)
    principal_payment_due = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    interest_payment_due = models.DecimalField(max_digits=12, decimal_places=2, default=0)



class Post(models.Model):
    title = models.CharField(max_length=100)
    content = models.TextField()
    date_posted = models.DateTimeField(auto_now_add=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.title


    def get_absolute_url(self):
        return reverse("post-detail", kwargs={"pk": self.pk})