from django import template
from django.contrib.humanize.templatetags.humanize import intcomma
from django.utils.safestring import mark_safe
from game.icons import ICONS, TOY_ICONS, DEFAULT_TOY_ICON, TOY_COLORS, DEFAULT_TOY_COLOR

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
    try:
        val = round(float(value), 2)
    except (ValueError, TypeError):
        return value

    formatted_val = format(abs(val), ".0%")

    if val < 0:
        return f"({formatted_val})"

    return formatted_val


@register.filter
def toy_icon(toy_name):
    name = (toy_name or "").lower()
    for keyword, emoji in TOY_ICONS.items():
        if keyword in name:
            return emoji
    return DEFAULT_TOY_ICON

TOY_COLORS = {
    "kite": "#228be6",
    "yo-yo": "#fa5252",
    "yoyo": "#fa5252",
    "bike": "#2f9e44",
    "bicycle": "#2f9e44",
}

DEFAULT_TOY_COLOR = "#868e96"


@register.filter
def toy_color(toy_name):
    name = (toy_name or "").lower()
    for keyword, color in TOY_COLORS.items():
        if keyword in name:
            return color
    return DEFAULT_TOY_COLOR


@register.simple_tag
def icon(key):
    return ICONS.get(key, "")