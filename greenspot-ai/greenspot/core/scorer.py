"""
Pareto Arbitrage Scorer.
Balances Spot cost vs. Carbon intensity to find the global sweet spot.
Formula: Score = w_cost * norm(cost) + w_carbon * norm(carbon)
"""

from typing import List, Optional
import numpy as np
from greenspot.schemas import RegionCandidate, CloudProvider
from greenspot.core.carbon import CarbonTelemetryClient, REGIONAL_GRID_TELEMETRY
from greenspot.core.pricing import SpotPricingClient

class ArbitrageScorer:
    def __init__(self, carbon_client: Optional[CarbonTelemetryClient] = None, pricing_client: Optional[SpotPricingClient] = None):
        self.carbon_client = carbon_client or CarbonTelemetryClient()
        self.pricing_client = pricing_client or SpotPricingClient()

    async def rank_candidates(
        self,
        instance_type: str = "g4dn.xlarge",
        carbon_weight: float = 0.5,
        max_budget_usd: Optional[float] = None,
        estimated_hours: float = 2.0
    ) -> List[RegionCandidate]:
        """
        Gathers regional price and carbon telemetry across all availability zones,
        computes normalized composite Pareto scores, and ranks candidates.
        """
        regions = self.carbon_client.get_all_regions()
        candidates: List[RegionCandidate] = []

        for region in regions:
            carbon_info = await self.carbon_client.get_regional_carbon(region)
            pricing_info = self.pricing_client.get_spot_pricing(region, instance_type)

            # Check budget constraint if provided
            total_estimated_spot_cost = pricing_info["spot_price_usd"] * estimated_hours
            if max_budget_usd and total_estimated_spot_cost > max_budget_usd:
                continue

            candidates.append(RegionCandidate(
                cloud_provider=CloudProvider.AWS,
                region_id=region,
                region_name=carbon_info.get("region_name", region),
                country=carbon_info.get("country", "GLOBAL"),
                instance_type=instance_type,
                vram_gb=pricing_info["vram_gb"],
                vcpus=pricing_info["vcpus"],
                ram_gb=pricing_info["ram_gb"],
                spot_price_usd_per_hr=pricing_info["spot_price_usd"],
                ondemand_price_usd_per_hr=pricing_info["ondemand_price_usd"],
                discount_pct=pricing_info["discount_pct"],
                carbon_intensity_gco2_per_kwh=carbon_info["carbon_intensity"],
                clean_energy_pct=carbon_info["clean_energy_pct"],
                primary_energy_source=carbon_info["primary_source"],
            ))

        if not candidates:
            return []

        # Vectorized Pareto Scoring
        costs = np.array([c.spot_price_usd_per_hr for c in candidates])
        carbons = np.array([c.carbon_intensity_gco2_per_kwh for c in candidates])

        # Min-max normalization
        cost_range = (costs.max() - costs.min()) if costs.max() != costs.min() else 1.0
        carbon_range = (carbons.max() - carbons.min()) if carbons.max() != carbons.min() else 1.0

        norm_costs = (costs - costs.min()) / cost_range
        norm_carbons = (carbons - carbons.min()) / carbon_range

        w_carbon = float(np.clip(carbon_weight, 0.0, 1.0))
        w_cost = 1.0 - w_carbon

        composite_scores = (w_cost * norm_costs) + (w_carbon * norm_carbons)

        for i, cand in enumerate(candidates):
            cand.composite_score = round(float(composite_scores[i]), 4)

        # Sort ascending (lower score = superior balance)
        candidates.sort(key=lambda x: x.composite_score)

        for rank_idx, cand in enumerate(candidates, start=1):
            cand.rank = rank_idx

        return candidates
