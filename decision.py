import datetime
from typing import Any, Dict, List, Optional, Tuple
from decay import quality_on_day


def evaluate_options(
    crop: str,
    quantity_kg: float,
    harvest_date: datetime.date,
    q0: float,
    temp_c: float,
    markets_data: List[Dict[str, Any]],
    selected_markets: Optional[List[str]] = None,
) -> Tuple[List[Dict[str, Any]], Optional[Dict[str, Any]], str]:
    """Evaluate selling options across markets and days (harvest day to +6 days).
    
    Args:
        crop: 'Tomato' or 'Onion'.
        quantity_kg: Quantity in kg (e.g., 500).
        harvest_date: Date of harvest.
        q0: Initial quality at harvest (50 to 100).
        temp_c: Storage temperature in °C for held produce.
        markets_data: List of market dictionaries from mock data.
        selected_markets: Optional list of market names to include.
        
    Returns:
        (options, recommendation, reason_text)
    """
    options: List[Dict[str, Any]] = []
    
    if not markets_data:
        return [], None, "No market data available."

    for market_entry in markets_data:
        # Robust validation: skip invalid or missing market structures
        if not isinstance(market_entry, dict):
            continue

        market_name = market_entry.get("name")
        if not market_name:
            continue

        if selected_markets is not None and market_name not in selected_markets:
            continue

        transport_cost = market_entry.get("transport_cost_per_kg")
        if transport_cost is None:
            continue
        try:
            transport_cost = float(transport_cost)
        except (ValueError, TypeError):
            continue

        # Support both 'price_per_kg' and 'prices' keys
        prices_dict = market_entry.get("price_per_kg") or market_entry.get("prices")
        if not isinstance(prices_dict, dict):
            continue

        # Look up crop prices case-insensitively
        crop_prices = None
        for key, prices_list in prices_dict.items():
            if str(key).strip().lower() == crop.strip().lower():
                crop_prices = prices_list
                break

        # A market with zero price-days or missing data is skipped and does not crash
        if not crop_prices or not isinstance(crop_prices, list) or len(crop_prices) == 0:
            continue

        # Evaluate each day from day 0 (harvest day) up to day 6 (7 days total)
        num_days = min(7, len(crop_prices))
        for days_held in range(num_days):
            price_val = crop_prices[days_held]
            if price_val is None:
                continue
            try:
                price = float(price_val)
            except (ValueError, TypeError):
                continue

            target_date = harvest_date + datetime.timedelta(days=days_held)

            # Quality calculation: for days_held == 0, quality is q0.
            # For days_held > 0, storage temperature temp_c is used.
            quality = quality_on_day(
                q0=q0,
                crop=crop,
                temp_c=temp_c,
                days=days_held
            )

            gross_per_kg = (quality / 100.0) * price
            net_per_kg = gross_per_kg - transport_cost
            total_net = net_per_kg * float(quantity_kg)

            options.append({
                "market": market_name,
                "category": market_entry.get("category", "General Mandi"),
                "distance_km": market_entry.get("distance_km", 0),
                "daily_volume_tons": market_entry.get("daily_volume_tons", 0),
                "buyer_demand": market_entry.get("buyer_demand", "Normal"),
                "day": target_date.strftime("%a, %b %d"),
                "day_name": target_date.strftime("%A"),
                "date": target_date,
                "days_held": days_held,
                "quality_on_arrival": round(quality, 1),
                "price": round(price, 2),
                "transport_cost": round(transport_cost, 2),
                "gross_per_kg": round(gross_per_kg, 2),
                "net_per_kg": round(net_per_kg, 2),
                "total_net": round(total_net, 2),
            })

    if not options:
        return [], None, "No viable selling options found with available market data."

    # Sort options: highest net_per_kg first; ties broken by selling sooner (lower days_held)
    options.sort(key=lambda opt: (-opt["net_per_kg"], opt["days_held"], opt["transport_cost"]))

    recommendation = options[0]
    reason_text = generate_reason(recommendation, options)

    return options, recommendation, reason_text


def generate_reason(recommendation: Dict[str, Any], options: List[Dict[str, Any]]) -> str:
    """Generate a plain-language explanation for why this option is recommended."""
    best_market = recommendation["market"]
    best_day = recommendation["day_name"]
    best_net = recommendation["net_per_kg"]
    days_held = recommendation["days_held"]

    # Identify today's options (days_held == 0)
    today_options = [opt for opt in options if opt["days_held"] == 0]

    if days_held == 0:
        return (
            f"Selling today at {best_market} gives ₹{best_net:.1f}/kg. "
            "Holding produce longer does not overcome quality loss and transport costs."
        )

    # Baseline comparison: prefer 'Village Market' today if present, else best today option
    village_today = next(
        (opt for opt in today_options if "village" in opt["market"].lower()),
        None
    )
    baseline = village_today if village_today else (today_options[0] if today_options else None)

    if baseline:
        diff = best_net - baseline["net_per_kg"]
        diff_str = f"about ₹{diff:.1f} more than" if diff > 0 else "comparable to"
        return (
            f"{best_market} on {best_day} gives ₹{best_net:.1f}/kg, "
            f"{diff_str} selling today at {baseline['market']}, "
            "after transport and expected spoilage."
        )

    return (
        f"{best_market} on {best_day} gives the highest expected return of "
        f"₹{best_net:.1f}/kg after transport and expected spoilage."
    )
