"""
Unit tests for GreenSpot AI FinOps & Carbon Data Layer.
Verifies:
1. boto3 AWS Spot Price History fetching with mock credentials & graceful fallback.
2. Expanded instance types (g5.2xlarge, a100, p4d.24xlarge, t4g.xlarge Graviton).
3. Historical trend modeling & preemption eviction risk calculation.
4. Expanded global regions (Sydney, Sao Paulo, Cape Town, Tokyo, Paris, N. California).
5. Expanded Electricity Maps zone mapping.
6. Diurnal solar/wind fluctuation modeling based on regional time of day.
"""

import pytest
import asyncio
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock
from botocore.exceptions import ClientError, EndpointConnectionError

from greenspot.core.pricing import (
    SpotPricingClient,
    INSTANCE_SPECS,
    INSTANCE_TYPE_ALIASES,
    REGIONAL_SPOT_DISCOUNTS,
)
from greenspot.core.carbon import (
    CarbonTelemetryClient,
    REGIONAL_GRID_TELEMETRY,
)
from greenspot.core.scorer import ArbitrageScorer


# ============================================================================
# 1. Instance Types & Specification Tests
# ============================================================================

def test_expanded_instance_types():
    """Verifies that all requested instance types exist with accurate specs."""
    client = SpotPricingClient(use_aws_live_api=False)

    # g5.2xlarge
    g5_2x = client.get_instance_spec("g5.2xlarge")
    assert g5_2x["vcpus"] == 8
    assert g5_2x["ram_gb"] == 32
    assert g5_2x["vram_gb"] == 24
    assert "A10G" in g5_2x["gpu_type"]
    assert g5_2x["ondemand_price"] > 1.0

    # p4d.24xlarge (8x A100)
    p4d = client.get_instance_spec("p4d.24xlarge")
    assert p4d["vcpus"] == 96
    assert p4d["ram_gb"] == 1152
    assert p4d["vram_gb"] == 320
    assert "A100" in p4d["gpu_type"]
    assert p4d["ondemand_price"] > 30.0

    # a100 alias
    a100 = client.get_instance_spec("a100")
    assert a100["vcpus"] == 96
    assert a100["vram_gb"] == 320
    assert a100["ondemand_price"] == p4d["ondemand_price"]

    # t4g.xlarge (Graviton)
    t4g = client.get_instance_spec("t4g.xlarge")
    assert t4g["vcpus"] == 4
    assert t4g["ram_gb"] == 16
    assert t4g["vram_gb"] == 0
    assert "Graviton" in t4g["gpu_type"]
    assert t4g["ondemand_price"] < 0.20

    # Unknown instance type falls back safely
    unknown = client.get_instance_spec("nonexistent.instance")
    assert unknown == INSTANCE_SPECS["g4dn.xlarge"]


# ============================================================================
# 2. Boto3 AWS Live Spot Price Fetching & Fallback Tests
# ============================================================================

def test_boto3_spot_pricing_fetch_success():
    """Tests live boto3 spot price fetching when AWS credentials/client succeed."""
    now = datetime.now(timezone.utc)
    mock_history = [
        {
            "AvailabilityZone": "us-west-2a",
            "InstanceType": "g4dn.xlarge",
            "ProductDescription": "Linux/UNIX",
            "SpotPrice": "0.1580",
            "Timestamp": now - timedelta(minutes=10),
        },
        {
            "AvailabilityZone": "us-west-2b",
            "InstanceType": "g4dn.xlarge",
            "ProductDescription": "Linux/UNIX",
            "SpotPrice": "0.1490",  # cheaper AZ
            "Timestamp": now - timedelta(minutes=5),
        },
        {
            "AvailabilityZone": "us-west-2c",
            "InstanceType": "g4dn.xlarge",
            "ProductDescription": "Linux/UNIX",
            "SpotPrice": "0.1620",
            "Timestamp": now - timedelta(minutes=2),
        },
    ]

    mock_ec2 = MagicMock()
    mock_ec2.describe_spot_price_history.return_value = {"SpotPriceHistory": mock_history}

    client = SpotPricingClient(
        use_aws_live_api=True,
        ec2_client_factory=lambda region: mock_ec2,
    )

    pricing = client.get_spot_pricing("us-west-2", "g4dn.xlarge")
    assert pricing["pricing_source"] == "aws_boto3"
    # Should pick the cheapest availability zone
    assert pricing["spot_price_usd"] == 0.1490
    assert pricing["discount_pct"] > 60.0
    assert "us-west-2b" in pricing["availability_zones"]
    assert pricing["availability_zones"]["us-west-2b"] == 0.1490
    assert pricing["historical_trend"]["sample_count"] == 3


def test_boto3_spot_pricing_client_error_fallback():
    """Verifies graceful fallback to calibrated model when AWS API call raises ClientError."""
    mock_ec2 = MagicMock()
    mock_ec2.describe_spot_price_history.side_effect = ClientError(
        {"Error": {"Code": "AuthFailure", "Message": "AWS was not able to validate the provided access credentials"}},
        "DescribeSpotPriceHistory"
    )

    client = SpotPricingClient(
        use_aws_live_api=True,
        ec2_client_factory=lambda region: mock_ec2,
    )

    # Should not raise; must seamlessly fall back
    pricing = client.get_spot_pricing("us-west-2", "t4g.xlarge")
    assert pricing["pricing_source"] == "calibrated_model"
    assert pricing["spot_price_usd"] > 0
    assert pricing["discount_pct"] > 0
    assert pricing["historical_trend"]["sample_count"] > 0


def test_boto3_spot_pricing_connection_error_fallback():
    """Verifies graceful fallback when AWS endpoint connection fails."""
    mock_ec2 = MagicMock()
    mock_ec2.describe_spot_price_history.side_effect = EndpointConnectionError(
        endpoint_url="https://ec2.us-west-2.amazonaws.com"
    )

    client = SpotPricingClient(
        use_aws_live_api=True,
        ec2_client_factory=lambda region: mock_ec2,
    )

    pricing = client.get_spot_pricing("us-west-2", "g5.2xlarge")
    assert pricing["pricing_source"] == "calibrated_model"
    assert pricing["instance_type"] == "g5.2xlarge"
    assert pricing["spot_price_usd"] < pricing["ondemand_price_usd"]


def test_boto3_spot_pricing_empty_history_fallback():
    """Verifies graceful fallback when AWS returns empty history."""
    mock_ec2 = MagicMock()
    mock_ec2.describe_spot_price_history.return_value = {"SpotPriceHistory": []}

    client = SpotPricingClient(
        use_aws_live_api=True,
        ec2_client_factory=lambda region: mock_ec2,
    )

    pricing = client.get_spot_pricing("us-west-2", "a100")
    assert pricing["pricing_source"] == "calibrated_model"
    assert pricing["instance_type"] == "a100"
    assert pricing["ondemand_price_usd"] == 32.77


# ============================================================================
# 3. Historical Trend Modeling & FinOps Analytics Tests
# ============================================================================

def test_historical_trend_rising_direction():
    """Verifies detection of rising price trend."""
    client = SpotPricingClient(use_aws_live_api=False)
    now = datetime.now(timezone.utc)

    # Prices steadily increase from 0.10 to 0.20
    history = [
        {"timestamp": (now - timedelta(hours=i)).isoformat(), "price": 0.10 + (24 - i) * 0.004}
        for i in range(24, -1, -1)
    ]
    trend = client.model_historical_trend(history, ondemand_price=0.50)
    assert trend["trend_direction"] == "rising"
    assert trend["slope_usd_per_hr"] > 0
    assert trend["max_price"] > trend["min_price"]


def test_historical_trend_falling_direction():
    """Verifies detection of falling price trend."""
    client = SpotPricingClient(use_aws_live_api=False)
    now = datetime.now(timezone.utc)

    # Prices steadily decrease
    history = [
        {"timestamp": (now - timedelta(hours=i)).isoformat(), "price": 0.25 - (24 - i) * 0.005}
        for i in range(24, -1, -1)
    ]
    trend = client.model_historical_trend(history, ondemand_price=0.50)
    assert trend["trend_direction"] == "falling"
    assert trend["slope_usd_per_hr"] < 0


def test_historical_trend_eviction_risk_high_vs_low():
    """Verifies eviction risk estimation based on price proximity to on-demand and volatility."""
    client = SpotPricingClient(use_aws_live_api=False)

    # Case A: Spot price is 85% of on-demand price -> high eviction risk
    high_risk_history = [{"price": 0.85}, {"price": 0.88}, {"price": 0.90}]
    trend_high = client.model_historical_trend(high_risk_history, ondemand_price=1.0)
    assert trend_high["eviction_risk"] == "high"
    assert trend_high["stability_score"] <= 0.40

    # Case B: Spot price is 25% of on-demand price with minimal variance -> low eviction risk
    low_risk_history = [{"price": 0.25}, {"price": 0.251}, {"price": 0.249}]
    trend_low = client.model_historical_trend(low_risk_history, ondemand_price=1.0)
    assert trend_low["eviction_risk"] == "low"
    assert trend_low["stability_score"] >= 0.80


def test_get_spot_price_history_time_series():
    """Verifies generation of 24h calibrated historical series."""
    client = SpotPricingClient(use_aws_live_api=False)
    res = client.get_spot_price_history("eu-north-1", "t4g.xlarge", hours=24)
    assert res["region_id"] == "eu-north-1"
    assert len(res["history"]) == 25  # 24 hours back down to 0
    assert "trend" in res
    assert res["trend"]["sample_count"] == 25
    assert res["trend"]["mean_price"] > 0


# ============================================================================
# 4. Regional Carbon Telemetry & Diurnal Modeling Tests
# ============================================================================

def test_expanded_six_regions_exist():
    """Verifies the addition of the 6 new global regions in carbon telemetry."""
    client = CarbonTelemetryClient()
    all_regions = client.get_all_regions()

    # Total regions must be 15 (original 9 + 6 new)
    assert len(all_regions) >= 15

    new_regions = [
        "ap-southeast-2",  # Sydney
        "sa-east-1",       # Sao Paulo
        "af-south-1",      # Cape Town
        "ap-northeast-1",  # Tokyo
        "eu-west-3",       # Paris
        "us-west-1",       # N. California
    ]

    for r in new_regions:
        assert r in all_regions
        assert r in REGIONAL_GRID_TELEMETRY
        assert r in REGIONAL_SPOT_DISCOUNTS
        data = REGIONAL_GRID_TELEMETRY[r]
        assert "region_name" in data
        assert "country" in data
        assert "primary_source" in data
        assert data["carbon_intensity"] > 0
        assert data["clean_energy_pct"] > 0


def test_expanded_electricity_maps_zone_mapping():
    """Verifies that all 15 regions map to accurate Electricity Maps zone identifiers."""
    client = CarbonTelemetryClient()

    expected_mappings = {
        "ap-southeast-2": "AU-NSW",
        "sa-east-1": "BR-CS",
        "af-south-1": "ZA",
        "ap-northeast-1": "JP-TK",
        "eu-west-3": "FR",
        "us-west-1": "US-CAL-CISO",
        "eu-north-1": "SE",
        "ca-central-1": "CA-QC",
        "eu-west-1": "IE",
        "eu-central-1": "DE",
        "us-west-2": "US-NW-PACW",
        "us-east-1": "US-MIDW-PJM",
        "us-east-2": "US-MIDW-PJM",
        "ap-southeast-1": "SG",
        "ap-south-1": "IN-WE",
    }

    for region, expected_zone in expected_mappings.items():
        assert client._map_aws_to_zone(region) == expected_zone


def test_diurnal_solar_fluctuation():
    """
    Verifies that daytime solar hours produce lower carbon intensity and
    higher clean energy percentage than evening peak hours in solar-rich regions.
    """
    client = CarbonTelemetryClient()

    # California (us-west-1, UTC-8):
    # Local 12:30 PM (solar peak) corresponds to 20:30 UTC
    solar_time = datetime(2026, 6, 15, 20, 30, tzinfo=timezone.utc)
    solar_telemetry = client.calculate_diurnal_carbon("us-west-1", timestamp=solar_time)

    # Local 19:30 (evening peaker peak) corresponds to 03:30 UTC next day
    peaker_time = datetime(2026, 6, 16, 3, 30, tzinfo=timezone.utc)
    peaker_telemetry = client.calculate_diurnal_carbon("us-west-1", timestamp=peaker_time)

    assert solar_telemetry["solar_active"] is True
    assert peaker_telemetry["peaker_active"] is True
    # Daytime solar must have lower carbon intensity than evening peakers
    assert solar_telemetry["carbon_intensity"] < peaker_telemetry["carbon_intensity"]
    # Daytime solar must have higher clean energy pct
    assert solar_telemetry["clean_energy_pct"] > peaker_telemetry["clean_energy_pct"]


def test_diurnal_wind_fluctuation():
    """Verifies that nighttime wind hours in Ireland (eu-west-1) boost clean energy."""
    client = CarbonTelemetryClient()

    # Dublin (eu-west-1, UTC+0):
    # Nighttime 02:30 UTC (wind peak)
    night_time = datetime(2026, 6, 15, 2, 30, tzinfo=timezone.utc)
    night_telemetry = client.calculate_diurnal_carbon("eu-west-1", timestamp=night_time)

    # Baseline
    base_clean = REGIONAL_GRID_TELEMETRY["eu-west-1"]["clean_energy_pct"]

    assert night_telemetry["wind_active"] is True
    # Clean energy during night wind surge must exceed baseline
    assert night_telemetry["clean_energy_pct"] > base_clean
    assert night_telemetry["carbon_intensity"] < REGIONAL_GRID_TELEMETRY["eu-west-1"]["carbon_intensity"]


def test_diurnal_forecast_24h():
    """Verifies 24-hour diurnal forecast generation."""
    client = CarbonTelemetryClient()
    forecast = client.get_diurnal_forecast_24h("ap-southeast-2")

    assert len(forecast) == 24
    for point in forecast:
        assert "timestamp" in point
        assert 0.0 <= point["local_hour"] <= 24.0
        assert point["carbon_intensity"] > 0
        assert point["clean_energy_pct"] > 0
        assert "diurnal_multiplier" in point


def test_async_get_regional_carbon():
    """Verifies async get_regional_carbon with diurnal fallback."""
    client = CarbonTelemetryClient()
    carbon = asyncio.run(client.get_regional_carbon("ap-southeast-2"))
    assert carbon["region_id"] == "ap-southeast-2"
    assert carbon["country"] == "AU"
    assert "carbon_intensity" in carbon
    assert "clean_energy_pct" in carbon
    assert isinstance(carbon["carbon_intensity"], int)


# ============================================================================
# 5. Arbitrage Scorer Integration with New FinOps Layer
# ============================================================================

def test_scorer_with_all_fifteen_regions_and_new_instances():
    """Verifies ArbitrageScorer evaluates all 15 regions and ranks new instance types."""
    scorer = ArbitrageScorer()

    for itype in ["t4g.xlarge", "g5.2xlarge", "a100"]:
        candidates = asyncio.run(scorer.rank_candidates(instance_type=itype, carbon_weight=0.5))
        assert len(candidates) >= 15
        assert candidates[0].rank == 1
        assert candidates[0].composite_score <= candidates[1].composite_score
        assert candidates[0].instance_type == itype
        assert candidates[0].spot_price_usd_per_hr > 0
