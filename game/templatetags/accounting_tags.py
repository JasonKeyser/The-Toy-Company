from django import template
from django.contrib.humanize.templatetags.humanize import intcomma
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter
def accounting(value):
    try:
        val = float(value)
    except (ValueError, TypeError):
        return value

    # 1. Handle Zero
    if val == 0:
        return "-"

    # Determine formatting: no decimals if whole number, 1 decimal if not
    if val == int(val):
        formatted_val = intcomma(abs(int(val)))
    else:
        formatted_val = intcomma(round(abs(val), 1))

    # 2. Handle Negative (Red text, Parentheses, Dollar sign inside)
    if val < 0:
        return mark_safe(f'<span style="color: red;">(${formatted_val})</span>')

    # 3. Handle Positive
    return f"${formatted_val}"


@register.filter
def accounting_round(value):
    try:
        val = float(value)
    except (ValueError, TypeError):
        return value

    # 1. Handle Zero
    if val == 0:
        return "-"

    formatted_val = intcomma(abs(int(val)))

    # 2. Handle Negative (Red text, Parentheses, Dollar sign inside)
    if val < 0:
        return mark_safe(f'<span style="color: red;">(${formatted_val})</span>')

    # 3. Handle Positive
    return f"${formatted_val}"


@register.filter
def accounting_round_exp(value):
    try:
        val = float(value) * -1 #making it negative to reflect expenses as outflows
    except (ValueError, TypeError):
        return value

    # 1. Handle Zero
    if val == 0:
        return "-"

    formatted_val = intcomma(abs(int(val)))

    # 2. Handle Negative (Red text, Parentheses, Dollar sign inside)
    if val < 0:
        return mark_safe(f'<span>(${formatted_val})</span>')

    # 3. Handle Positive
    return f"${formatted_val}"


@register.filter
def percentage(value):
    return format( round(value, 2), "%")