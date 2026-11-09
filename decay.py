import math

# ==============================================================================
# QUALITY DECAY CONSTANTS (Placeholders)
# ==============================================================================
# NOTE: The base decay constants below represent placeholder rates calibrated at
# a reference temperature of 25°C. These values should be calibrated with
# empirical data from post-harvest laboratory trials or cold-chain studies.
BASE_DECAY_RATES = {
    "Tomato": 0.08,
    "Onion": 0.03,
}

REFERENCE_TEMP_C = 25.0
TEMP_COEFF_DOUBLING_INTERVAL = 10.0  # Quality loss rate doubles every 10°C increase


def get_effective_decay_rate(crop: str, temp_c: float) -> float:
    """Calculate temperature-adjusted decay rate k_eff.
    
    Formula: k_eff = k_base * 2 ** ((T - 25) / 10)
    """
    # Normalize crop name lookup
    crop_normalized = crop.strip().capitalize()
    if crop_normalized not in BASE_DECAY_RATES:
        raise ValueError(
            f"Unsupported crop '{crop}'. Supported crops: {list(BASE_DECAY_RATES.keys())}"
        )
    
    k_base = BASE_DECAY_RATES[crop_normalized]
    temp_factor = 2.0 ** ((float(temp_c) - REFERENCE_TEMP_C) / TEMP_COEFF_DOUBLING_INTERVAL)
    return k_base * temp_factor


def quality_on_day(q0: float, crop: str, temp_c: float, days: float) -> float:
    """Calculate expected quality percentage on a given day since harvest.
    
    Formula: q(t) = q0 * exp(-k_eff * t)
    
    Args:
        q0: Initial quality at harvest (0 to 100).
        crop: Crop name ('Tomato' or 'Onion').
        temp_c: Storage temperature in Celsius.
        days: Elapsed days since harvest (t >= 0).
        
    Returns:
        float: Expected quality on arrival (clamped between 0.0 and 100.0).
    """
    days = max(0.0, float(days))
    if days == 0.0:
        return float(min(100.0, max(0.0, q0)))

    k_eff = get_effective_decay_rate(crop, temp_c)
    quality = float(q0) * math.exp(-k_eff * days)
    
    # Clamp between 0.0 and 100.0
    return float(min(100.0, max(0.0, quality)))
