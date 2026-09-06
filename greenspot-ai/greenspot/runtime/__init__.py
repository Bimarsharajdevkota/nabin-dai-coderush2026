"""
GreenSpot AI Runtime Resilience & Checkpointing Layer.
Provides spot instance preemption detection, automated S3 multipart checkpointing,
and the @checkpoint_protect decorator for machine learning workloads.
"""

from greenspot.runtime.checkpoint import (
    CheckpointManager,
    S3Uploader,
    CheckpointContext,
    checkpoint_protect,
    PreemptionInterrupted,
    serialize_checkpoint_payload,
)
from greenspot.runtime.preemption import (
    IMDSv2Client,
    SpotPreemptionWatcher,
    SimulatedInterruptionGenerator,
    create_simulated_interruption,
    simulate_interruption,
)
from greenspot.runtime.launcher import WorkloadLauncher, CapacityException

__all__ = [
    "CheckpointManager",
    "S3Uploader",
    "CheckpointContext",
    "checkpoint_protect",
    "PreemptionInterrupted",
    "serialize_checkpoint_payload",
    "IMDSv2Client",
    "SpotPreemptionWatcher",
    "SimulatedInterruptionGenerator",
    "create_simulated_interruption",
    "simulate_interruption",
    "WorkloadLauncher",
    "CapacityException",
]
