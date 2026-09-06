"""
Shared Pydantic domain models for GreenSpot AI.
Contract between Person 1 (FinOps Scorer), Person 2 (Runtime/Launcher), and Person 3 (CLI/API).
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class CloudProvider(str, Enum):
    AWS = "aws"
    GCP = "gcp"
    AZURE = "azure"


class WorkloadType(str, Enum):
    AI_TRAINING = "ai_training"
    BATCH_ETL = "batch_etl"
    RENDERING = "rendering"
    GENERAL_COMPUTE = "general_compute"


class RegionCandidate(BaseModel):
    cloud_provider: CloudProvider = Field(default=CloudProvider.AWS, description="Cloud provider")
    region_id: str = Field(..., description="Region code e.g. eu-north-1, us-east-1")
    region_name: str = Field(..., description="Human readable region name e.g. Stockholm, Sweden")
    country: str = Field(..., description="Country code e.g. SE, US")
    instance_type: str = Field(..., description="Instance type e.g. g4dn.xlarge")
    vram_gb: int = Field(default=16, description="VRAM in GB")
    vcpus: int = Field(default=4, description="Virtual CPUs")
    ram_gb: int = Field(default=16, description="System RAM in GB")
    
    # Pricing
    spot_price_usd_per_hr: float = Field(..., description="Real-time spot instance price per hour")
    ondemand_price_usd_per_hr: float = Field(..., description="Standard on-demand retail price")
    discount_pct: float = Field(..., description="Percentage discount vs on-demand")
    
    # Carbon / Energy
    carbon_intensity_gco2_per_kwh: int = Field(..., description="Current grid carbon intensity (gCO2eq/kWh)")
    clean_energy_pct: float = Field(default=90.0, description="Percentage of clean/renewable energy in regional grid")
    primary_energy_source: str = Field(default="Hydro", description="Dominant energy generation source")
    
    # Scoring
    composite_score: float = Field(default=0.0, description="Arbitrage score (lower is better)")
    rank: int = Field(default=1, description="Rank position (1 is best)")


class JobSubmission(BaseModel):
    task_command: str = Field(..., description="The executable command e.g. 'python train_bert.py'")
    max_budget_usd: float = Field(default=25.0, description="Max budget allocated for this job")
    estimated_duration_hours: float = Field(default=2.0, description="Estimated duration in hours")
    preferred_instance_type: str = Field(default="g4dn.xlarge", description="Target instance class")
    carbon_weight: float = Field(
        default=0.5, 
        ge=0.0, 
        le=1.0, 
        description="Weight for carbon vs price optimization. 0.0=Cheapest only, 1.0=Cleanest only, 0.5=Balanced"
    )
    enable_checkpointing: bool = Field(default=True, description="Enable automated S3 checkpoint protection")
    s3_checkpoint_bucket: Optional[str] = Field(default="greenspot-checkpoints-prod", description="Target S3 bucket for weights")


class JobStatus(str, Enum):
    QUEUED = "queued"
    SCORING = "scoring"
    LAUNCHING = "launching"
    RUNNING = "running"
    PREEMPTED = "preempted"
    RESUMING = "resuming"
    COMPLETED = "completed"
    FAILED = "failed"


class PreemptionEvent(BaseModel):
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    evicted_region: str
    evicted_instance_id: str
    checkpoint_size_mb: float
    sync_duration_seconds: float
    resumed_region: str
    resumed_instance_id: str


class JobReceipt(BaseModel):
    job_id: str
    task_command: str
    status: JobStatus = JobStatus.COMPLETED
    started_at: datetime
    finished_at: datetime
    runtime_hours: float
    
    # Financial metrics
    executed_provider: CloudProvider
    executed_region: str
    executed_region_name: str
    executed_instance_type: str
    actual_spot_cost_usd: float
    baseline_ondemand_cost_usd: float
    total_savings_usd: float
    savings_percentage: float
    
    # Carbon metrics
    carbon_intensity_gco2_kwh: int
    carbon_emitted_gco2: float
    carbon_avoided_gco2: float
    clean_energy_percentage: float
    primary_energy_source: str
    equivalent_gas_car_km_avoided: float
    
    # Preemption resilience
    preemptions_handled: int = 0
    preemption_history: List[PreemptionEvent] = []
    checkpoint_verification_hash: str = Field(default="sha256-a9f87c123d4e")


class ESGStats(BaseModel):
    total_carbon_avoided_gco2: float = Field(..., description="Total carbon avoided across all jobs in gCO2eq")
    total_cost_saved_usd: float = Field(..., description="Total cloud costs saved in USD")
    total_jobs_executed: int = Field(..., description="Total number of jobs executed")
    average_clean_energy_pct: float = Field(..., description="Average clean energy percentage across all jobs")
    total_gas_car_km_avoided: float = Field(..., description="Equivalent gasoline car kilometers avoided")
    total_actual_cost_usd: float = Field(default=0.0, description="Total actual spot instance costs incurred")
    total_baseline_cost_usd: float = Field(default=0.0, description="Total retail on-demand baseline costs")
    average_savings_pct: float = Field(default=0.0, description="Average savings percentage across all jobs")
    total_preemptions_handled: int = Field(default=0, description="Total preemptions handled with zero data loss")
