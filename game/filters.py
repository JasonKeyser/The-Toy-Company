import django_filters
from .models import Player

class PlayerFilter(django_filters.FilterSet):

    company_name = django_filters.ChoiceFilter(
        choices=[],  # populated per-user below
        empty_label="All Factories",
    )

    status = django_filters.ChoiceFilter(
        choices=[],  # populated per-user below
        empty_label="All Statuses",
    )


    Min_Turn_Number = django_filters.NumberFilter(field_name='turn_number', lookup_expr='gte')
    Min_Factory_Space = django_filters.NumberFilter(field_name='factory_space', lookup_expr='gte')

    class Meta:
        model = Player
        fields = ['status', 'lost_reason', 'company_name', 'mode', 'difficulty', 'equipment_bought']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        names = (
            self.queryset
            .order_by('company_name')
            .values_list('company_name', flat=True)
            .distinct()
        )
        self.filters['company_name'].extra['choices'] = [(n, n) for n in names]


        statuses = (
            self.queryset
            .order_by('status')
            .values_list('status', flat=True)
            .distinct()
        )
        self.filters['status'].extra['choices'] = [(s, s) for s in statuses]




        for field in self.form.fields.values():
            existing = field.widget.attrs.get('class', '')
            field.widget.attrs['class'] = (existing + ' form-control form-control-sm').strip()



