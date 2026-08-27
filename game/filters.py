import django_filters
from .models import Player

class PlayerFilter(django_filters.FilterSet):

    Min_Turn_Number = django_filters.NumberFilter(field_name='turn_number', lookup_expr='gte')
    Min_Factory_Space = django_filters.NumberFilter(field_name='factory_space', lookup_expr='gte')


    class Meta:
        model = Player
        fields = ['status', 'lost_reason', 'company_name', 'mode', 'difficulty', 'equipment_bought']



