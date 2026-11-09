import pytest
from alerts import generate_alerts


def test_alerts_under_200_characters_today():
    """Alert text stays strictly under 200 characters for sell today option."""
    rec = {
        "market": "Village Market",
        "day_name": "Monday",
        "days_held": 0,
        "net_per_kg": 19.5,
        "total_net": 9750.0,
    }
    en_alert, ta_alert = generate_alerts(rec, crop="Tomato")

    assert len(en_alert) <= 200
    assert len(ta_alert) <= 200
    assert "Village Market" in en_alert
    assert "19.5" in en_alert
    assert "Village Market" in ta_alert


def test_alerts_under_200_characters_hold():
    """Alert text stays strictly under 200 characters for hold & sell option."""
    rec = {
        "market": "City Agricultural Produce Market Committee",
        "day_name": "Wednesday",
        "days_held": 3,
        "net_per_kg": 25.5,
        "total_net": 12750.0,
    }
    en_alert, ta_alert = generate_alerts(rec, crop="Onion")

    assert len(en_alert) <= 200
    assert len(ta_alert) <= 200
    assert "Wednesday" in en_alert or "Wed" in en_alert
    assert "வெங்காயம்" in ta_alert
    assert "புதன்" in ta_alert


def test_alerts_empty_recommendation():
    """Alert generation should handle None gracefully."""
    en_alert, ta_alert = generate_alerts(None, crop="Tomato")
    assert len(en_alert) <= 200
    assert len(ta_alert) <= 200
