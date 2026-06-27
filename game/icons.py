TOY_ICONS = {"kite": "🪁", "yo-yo": "🪀", "bike": "🚲"}
DEFAULT_TOY_ICON = "🧸"
ICONS = {  # all other game icons, by descriptive key
    "toy_company": "🧸", "money": "💰", "warning": "⚠", "funding": "💵",
    "ad_boost": "📢", "investments": "🏗", "insurance": "🛡", "financing": "🏦",
    "production_planning": "📋", "turn_summary": "📊", "celebration": "🎉",
    "beach": "🏖️", "financial_history": "📈", "dice": "🎲",
    "disaster_loss": "💥", "no_disaster": "✅", "gross_profit_analysis": "📊",
    "ad_campaign_note": "📣", "boost_highlight": "🟡",
}


def get_toy_icon(toy_name):
    name = (toy_name or "").lower()
    for keyword, emoji in TOY_ICONS.items():
        if keyword in name:
            return emoji
    return DEFAULT_TOY_ICON


def get_toy_color(toy_name):
    name = (toy_name or "").lower()
    for keyword, color in TOY_COLORS.items():
        if keyword in name:
            return color
    return DEFAULT_TOY_COLOR



TOY_COLORS = {
    "kite": "#228be6",
    "yo-yo": "#fa5252",
    "yoyo": "#fa5252",
    "bike": "#2f9e44",
    "bicycle": "#2f9e44",
}

DEFAULT_TOY_COLOR = "#868e96"