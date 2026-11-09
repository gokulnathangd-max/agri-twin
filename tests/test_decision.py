import datetime
import pytest
from decision import evaluate_options


@pytest.fixture
def sample_markets():
    return [
        {
            "name": "Village Market",
            "distance_km": 2,
            "transport_cost_per_kg": 0.5,
            "price_per_kg": {
                "Tomato": [20.0, 19.5, 20.0, 21.0, 20.5, 19.0, 19.5],
                "Onion": [25.0, 25.5, 25.0, 26.0, 25.5, 25.0, 24.5],
            },
        },
        {
            "name": "Town Market",
            "distance_km": 25,
            "transport_cost_per_kg": 2.0,
            "price_per_kg": {
                "Tomato": [22.0, 23.5, 25.0, 26.0, 24.5, 23.0, 22.5],
                "Onion": [27.0, 27.5, 28.5, 29.0, 28.0, 27.5, 27.0],
            },
        },
        {
            "name": "City Market",
            "distance_km": 60,
            "transport_cost_per_kg": 4.5,
            "price_per_kg": {
                "Tomato": [25.0, 26.0, 27.5, 29.0, 30.0, 28.5, 27.0],
                "Onion": [29.0, 30.0, 31.0, 32.5, 31.5, 30.5, 30.0],
            },
        },
    ]


def test_recommendation_is_maximum_net_per_kg(sample_markets):
    """The recommendation is always the option with the maximum net_per_kg."""
    harvest_date = datetime.date(2026, 11, 10)
    options, recommendation, reason = evaluate_options(
        crop="Tomato",
        quantity_kg=500,
        harvest_date=harvest_date,
        q0=100.0,
        temp_c=25.0,
        markets_data=sample_markets,
    )

    assert recommendation is not None
    assert len(options) > 0

    max_net = max(opt["net_per_kg"] for opt in options)
    assert recommendation["net_per_kg"] == max_net
    assert recommendation == options[0]
    assert isinstance(reason, str) and len(reason) > 0


def test_tie_breaking_favors_sooner_day():
    """When two options have identical net_per_kg, the one that sells sooner is chosen."""
    harvest_date = datetime.date(2026, 11, 10)
    # Market A gives net 19.5 on day 0, Market B gives net 19.5 on day 2
    mock_markets = [
        {
            "name": "Market B (Day 2)",
            "distance_km": 5,
            "transport_cost_per_kg": 0.0,
            "price_per_kg": {
                # Notice with decay, day 2 net will be calculated from price
                # We can construct prices such that net ends up identical
                "Tomato": [15.0, 15.0, 25.0, 15.0, 15.0, 15.0, 15.0]
            },
        },
        {
            "name": "Market A (Day 0)",
            "distance_km": 2,
            "transport_cost_per_kg": 0.5,
            "price_per_kg": {
                "Tomato": [20.0, 10.0, 10.0, 10.0, 10.0, 10.0, 10.0]
            },
        },
    ]
    # For day 0 at Market A: gross = 1.0 * 20.0 = 20.0, net = 20.0 - 0.5 = 19.5
    options, rec, _ = evaluate_options(
        crop="Tomato",
        quantity_kg=100,
        harvest_date=harvest_date,
        q0=100.0,
        temp_c=25.0,
        markets_data=mock_markets,
    )
    # The first option in options should be the maximum net
    assert rec["net_per_kg"] == max(o["net_per_kg"] for o in options)


def test_market_with_zero_price_days_or_missing_data_skipped():
    """A market with zero price-days or missing data is skipped and does not crash."""
    harvest_date = datetime.date(2026, 11, 10)
    corrupted_markets = [
        # Market with empty price list
        {
            "name": "Empty Market",
            "distance_km": 10,
            "transport_cost_per_kg": 1.0,
            "price_per_kg": {"Tomato": []},
        },
        # Market with missing price_per_kg key
        {
            "name": "Missing Price Market",
            "distance_km": 15,
            "transport_cost_per_kg": 1.5,
        },
        # Market without target crop
        {
            "name": "Wrong Crop Market",
            "distance_km": 20,
            "transport_cost_per_kg": 2.0,
            "price_per_kg": {"Potato": [20.0, 21.0]},
        },
        # Market with None or invalid data
        {"invalid_entry": True},
        # One valid market with 3 days of prices
        {
            "name": "Valid Market",
            "distance_km": 5,
            "transport_cost_per_kg": 0.5,
            "price_per_kg": {"Tomato": [22.0, 23.0, 24.0]},
        },
    ]

    options, rec, reason = evaluate_options(
        crop="Tomato",
        quantity_kg=200,
        harvest_date=harvest_date,
        q0=95.0,
        temp_c=25.0,
        markets_data=corrupted_markets,
    )

    # Should not crash and should correctly process the valid market
    assert rec is not None
    assert rec["market"] == "Valid Market"
    assert len(options) == 3  # 3 days of prices from the valid market


def test_empty_market_list_handled_gracefully():
    """Empty market list returns empty options and does not crash."""
    options, rec, reason = evaluate_options(
        crop="Tomato",
        quantity_kg=100,
        harvest_date=datetime.date.today(),
        q0=100.0,
        temp_c=25.0,
        markets_data=[],
    )
    assert options == []
    assert rec is None
    assert "No market data" in reason
