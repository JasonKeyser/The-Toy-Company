from django import forms
from django.core.exceptions import ValidationError
from .models import AdvertisingProfile, Equipment

class FactoryExpansionForm(forms.Form):
    extra_space = forms.IntegerField(
        min_value=0,
        required=False,
        initial=0,
        label="Additional Factory Space",
        widget=forms.NumberInput(attrs={
            "class": "form-control",
            "placeholder": "0"
        })
    )

    def clean_extra_space(self):
        space = self.cleaned_data.get("extra_space") or 0
        return space

class AdvertisementCampaignForm(forms.Form):
    ad_campaign = forms.ModelChoiceField(
        queryset=AdvertisingProfile.objects.none(),
        required=False,
        label="Ad Campaign",
        empty_label="No advertisement"
    )

    def __init__(self, *args, difficulty=None, **kwargs):
        super().__init__(*args, **kwargs)
        if difficulty:
            self.fields['ad_campaign'].queryset = AdvertisingProfile.objects.filter(difficulty=difficulty)

    def clean_ad_campaign(self):
        ad = self.cleaned_data.get("ad_campaign") or 0
        return ad

class EquipmentForm(forms.Form):
    equipment = forms.ModelChoiceField(
        queryset= Equipment.objects.none(),
        required=False,
        label="Equipment",
        empty_label="No Equipment"
    )

    def __init__(self, *args, equipment_bought=False, **kwargs):
        super().__init__(*args, **kwargs)
        if equipment_bought:
            self.fields['equipment'].queryset = Equipment.objects.none()
            self.fields['equipment'].widget.attrs['disabled'] = True
            self.fields['equipment'].help_text = "Equipment already purchased."
        else:
            self.fields['equipment'].queryset = Equipment.objects.all()

    #need to add a check to make sure this is not purchased twice in a game
    def clean_equipment(self):
        equipment_purchased = self.cleaned_data.get("equipment") or 0
        return equipment_purchased


class LoanForm(forms.Form):
    borrowed_amount = forms.IntegerField(
        min_value=0,
        required=False,
        initial=0,
        label="Borrowed Amount",
        widget=forms.NumberInput(attrs={
            "class": "form-control",
            "placeholder": "0"
        })
    )

    def clean_borrowed_amount(self):
        borrowed = self.cleaned_data.get("borrowed_amount") or 0
        return borrowed





class InsuranceCoverageTakenForm(forms.Form):
    # Your form fields go here
    coverage_taken = forms.ChoiceField(
        label="Coverage Taken",
        choices=[("assume_risk","Assume Risk"), ("insure", "Insure")],
        required=False)

    def clean_coverage_taken(self):
        coverage = self.cleaned_data.get('coverage_taken', "assume_risk")
        return coverage == "insure"


class BaseCoverageFormSet(forms.BaseFormSet):
    def __init__(self, *args, **kwargs):
        # self.insurance_events = kwargs.pop("insurance_events", [])
        super().__init__(*args, **kwargs)

    def clean(self):
        """Cross-form validation for insurance coverage choices."""
        if any(self.errors):
            return

        # You could add cross-event validation here if needed in future,
        # e.g. a cap on how many events a player can insure per turn.
        # For now, each event is independent so no cross-form rules apply.
        pass


class UnitsManufacturedForm(forms.Form):
    # Your form fields go here
    units_to_manufacture = forms.IntegerField(min_value=0, initial=0, required=False, widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': "0"}))


    def clean_units_to_manufacture(self):
        units = self.cleaned_data.get('units_to_manufacture', 0)

        if units is None:
            return 0

        return units


class BaseUnitsFormSet(forms.BaseFormSet):
    def __init__(self, *args, **kwargs):
        # We pass factory_space into the formset from the view
        self.factory_space = kwargs.pop('factory_space', 1000)
        # self.max_cash_spend = kwargs.pop('max_cash_spend', 10000)
        super().__init__(*args, **kwargs)

    def clean(self):
        """Checks the total sum across all forms."""
        if any(self.errors):
            # Don't validate the total if individual rows already have errors
            return

        total_units = 0
        for form in self.forms:
            if form.cleaned_data:
                total_units += form.cleaned_data.get('units_to_manufacture', 0)

        if total_units > self.factory_space:
            raise ValidationError(
                f"Total production {total_units} exceeds your "
                f"factory space {self.factory_space}!"
            )