import pytest
from decay import quality_on_day, get_effective_decay_rate


def test_quality_at_day_zero_is_initial_quality():
    """Quality is 100 at day 0 when q0 is 100."""
    q_tomato = quality_on_day(100.0, "Tomato", temp_c=25.0, days=0)
    q_onion = quality_on_day(100.0, "Onion", temp_c=30.0, days=0)
    assert q_tomato == 100.0
    assert q_onion == 100.0

    # Also check with initial quality 80
    assert quality_on_day(80.0, "Tomato", temp_c=25.0, days=0) == 80.0


def test_quality_decreases_with_time():
    """Quality decreases monotonically as days increase."""
    q0 = 100.0
    temp = 25.0
    q_day1 = quality_on_day(q0, "Tomato", temp, days=1)
    q_day2 = quality_on_day(q0, "Tomato", temp, days=2)
    q_day5 = quality_on_day(q0, "Tomato", temp, days=5)

    assert q0 > q_day1 > q_day2 > q_day5


def test_quality_decreases_with_higher_temperature():
    """Quality decreases faster at higher temperatures."""
    q0 = 100.0
    days = 3.0
    q_cold = quality_on_day(q0, "Tomato", temp_c=15.0, days=days)
    q_ambient = quality_on_day(q0, "Tomato", temp_c=25.0, days=days)
    q_hot = quality_on_day(q0, "Tomato", temp_c=35.0, days=days)

    assert q_cold > q_ambient > q_hot


def test_crop_decay_rate_differences():
    """Tomato has a higher base decay rate than Onion."""
    q_tomato = quality_on_day(100.0, "Tomato", temp_c=25.0, days=4)
    q_onion = quality_on_day(100.0, "Onion", temp_c=25.0, days=4)
    assert q_onion > q_tomato


def test_unsupported_crop_raises_error():
    """Unsupported crops should raise ValueError."""
    with pytest.raises(ValueError):
        quality_on_day(100.0, "Papaya", temp_c=25.0, days=2)
