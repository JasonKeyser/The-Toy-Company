from django import template
register = template.Library()

@register.filter
def sum_attr(queryset, attr):
    return sum(getattr(obj, attr, 0) for obj in queryset)


@register.filter
def div(numerator, denominator):
    try:
        denominator = float(denominator)
        if denominator == 0:
            return 0
        return float(numerator) / denominator
    except (ValueError, TypeError):
        return 0