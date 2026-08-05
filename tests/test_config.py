"""Config is the one place `T_NOW` is defined, and every time-based split derives
from it. A silently wrong value here produces empty training frames rather than an
error, so the invariants are asserted rather than trusted."""

from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError

from src.config import Settings


def test_defaults_load() -> None:
    settings = Settings()
    assert settings.source_dataset == "bigquery-public-data.london_bicycles"
    assert settings.holidays_country == "GB"
    assert 10 <= settings.zone_count <= 30


def test_t_now_is_timezone_aware() -> None:
    assert Settings().t_now.tzinfo is not None


def test_naive_t_now_is_rejected() -> None:
    with pytest.raises(ValidationError, match="timezone-aware"):
        Settings(t_now=datetime(2023, 1, 1))


def test_future_t_now_is_rejected() -> None:
    """A future T_NOW pushes the train/validation/test windows past the end of the
    data, which yields empty frames instead of a failure."""
    tomorrow = datetime.now(UTC) + timedelta(days=1)
    with pytest.raises(ValidationError, match="must be in the past"):
        Settings(t_now=tomorrow)


@pytest.mark.parametrize("bad", [0.0, 1.0, -0.1, 1.5])
def test_promotion_thresholds_must_be_fractions(bad: float) -> None:
    with pytest.raises(ValidationError):
        Settings(mae_improvement_min=bad)


def test_promotion_defaults_match_architecture_doc() -> None:
    """architecture.md 5: improve MAE by >= 2%, degrade no segment by > 5%."""
    settings = Settings()
    assert settings.mae_improvement_min == 0.02
    assert settings.segment_degradation_max == 0.05
