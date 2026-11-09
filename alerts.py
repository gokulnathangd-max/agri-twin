from typing import Any, Dict, Optional, Tuple

# ==============================================================================
# TAMIL TEMPLATES & VOCABULARY (Placeholders)
# ==============================================================================
# NOTE: The Tamil templates and dictionary terms below are illustrative and
# designed for the prototype. They should be reviewed and verified by a native
# Tamil speaker before real-world deployment.
TAMIL_DICTIONARY = {
    "crops": {
        "Tomato": "தக்காளி",
        "Onion": "வெங்காயம்",
    },
    "days": {
        "Monday": "திங்கள்",
        "Tuesday": "செவ்வாய்",
        "Wednesday": "புதன்",
        "Thursday": "வியாழன்",
        "Friday": "வெள்ளி",
        "Saturday": "சனி",
        "Sunday": "ஞாயிறு",
    },
    "templates": {
        "hold": (
            "Agri-Twin: {crop} பயிரை {day} அன்று {market} சந்தையில் விற்கவும். "
            "நிகர விலை: ₹{net_per_kg}/கிலோ (மொத்தம் ₹{total_net})."
        ),
        "today": (
            "Agri-Twin: {crop} பயிரை இன்றே {market} சந்தையில் விற்கவும். "
            "நிகர விலை: ₹{net_per_kg}/கிலோ (மொத்தம் ₹{total_net})."
        ),
    },
}


def generate_alerts(
    recommendation: Optional[Dict[str, Any]],
    crop: str = "Tomato",
) -> Tuple[str, str]:
    """Generate English and Tamil alert messages from the recommendation.
    
    Both alerts are strictly formatted to remain under 200 characters for
    easy SMS / WhatsApp transmission to farmers.
    
    Args:
        recommendation: The chosen recommendation dictionary.
        crop: The crop name ('Tomato' or 'Onion').
        
    Returns:
        (english_alert, tamil_alert)
    """
    if not recommendation:
        en_fallback = "Agri-Twin: No selling recommendation available for selected inputs."
        ta_fallback = "Agri-Twin: பரிந்துரை ஏதும் இல்லை."
        return en_fallback, ta_fallback

    market = recommendation.get("market", "Local Market")
    day_name = recommendation.get("day_name", "Today")
    days_held = recommendation.get("days_held", 0)
    net_per_kg = recommendation.get("net_per_kg", 0.0)
    total_net = recommendation.get("total_net", 0.0)
    formatted_total = f"{int(round(total_net)):,}"

    # English Alert (under 200 chars)
    if days_held == 0:
        english_alert = (
            f"Agri-Twin: Sell {crop} today at {market} for best net "
            f"₹{net_per_kg:.1f}/kg (₹{formatted_total} total)."
        )
    else:
        english_alert = (
            f"Agri-Twin: Hold & sell {crop} at {market} on {day_name} for best net "
            f"₹{net_per_kg:.1f}/kg (₹{formatted_total} total)."
        )

    # Tamil Alert (under 200 chars)
    crop_tamil = TAMIL_DICTIONARY["crops"].get(crop.capitalize(), crop)
    day_tamil = TAMIL_DICTIONARY["days"].get(day_name, day_name)
    template_key = "today" if days_held == 0 else "hold"
    tamil_template = TAMIL_DICTIONARY["templates"][template_key]

    tamil_alert = tamil_template.format(
        crop=crop_tamil,
        market=market,
        day=day_tamil,
        net_per_kg=f"{net_per_kg:.1f}",
        total_net=formatted_total,
    )

    # Guard length under 200 characters
    if len(english_alert) > 200:
        english_alert = english_alert[:197] + "..."
    if len(tamil_alert) > 200:
        tamil_alert = tamil_alert[:197] + "..."

    return english_alert, tamil_alert
