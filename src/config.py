"""Central configuration.

`T_NOW` is the simulated present (docs/architecture.md §2). Training reads data
before it; the drift job replays data after it. Every time-based split derives
from this one value, which is why it is validated here rather than trusted.
"""

from datetime import UTC, datetime
from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Environment-overridable settings, prefixed `PEDAL_CAST_`."""

    model_config = SettingsConfigDict(
        env_prefix="PEDAL_CAST_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="forbid",
    )

    # --- GCP ---------------------------------------------------------------
    gcp_project_id: str = "pedal-cast-dev"
    gcp_region: str = "europe-west2"
    bq_dataset: str = "pedal_cast"

    # Set per Cloud Run revision, which is what makes a model deploy a new
    # revision and therefore a clean canary (docs/architecture.md §6).
    artifact_gcs_uri: str = ""

    # --- Source data -------------------------------------------------------
    # Placeholder pending Gate 0: the recency queries decide the dataset, and
    # the answer also fixes `t_now` and `holidays_country`.
    source_dataset: str = "bigquery-public-data.london_bicycles"
    source_trips_table: str = "cycle_hire"
    source_stations_table: str = "cycle_stations"
    holidays_country: str = "GB"

    t_now: datetime = datetime(2023, 1, 1, tzinfo=UTC)

    # --- Features ----------------------------------------------------------
    # 10-30 per docs/architecture.md §4; the real number comes from Week 1 EDA.
    zone_count: int = Field(default=20, ge=10, le=30)

    # --- Cost guardrail ----------------------------------------------------
    # Every BigQuery job carries this (docs/architecture.md §10.5).
    maximum_bytes_billed: int = Field(default=10 * 1024**3, gt=0)

    # --- Promotion rule ----------------------------------------------------
    # docs/architecture.md §5: a challenger must improve validation MAE by at
    # least this fraction, and degrade no segment by more than the other.
    mae_improvement_min: float = Field(default=0.02, gt=0, lt=1)
    segment_degradation_max: float = Field(default=0.05, gt=0, lt=1)

    @field_validator("t_now")
    @classmethod
    def _validate_t_now(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError(
                "T_NOW must be timezone-aware; a naive value makes split "
                "boundaries ambiguous across the DST changes in the data"
            )
        if value > datetime.now(UTC):
            raise ValueError(
                "T_NOW must be in the past. A future value pushes the "
                "train/validation/test windows beyond the end of the data, "
                "which yields empty frames instead of an error."
            )
        return value


@lru_cache
def get_settings() -> Settings:
    """Cached accessor, so validation runs once per process rather than at import."""
    return Settings()
