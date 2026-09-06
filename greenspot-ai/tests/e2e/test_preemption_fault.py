import pytest
from fastapi.testclient import TestClient
from greenspot.api.server import app

client = TestClient(app)

def test_simulate_preemption_fault():
    payload = {
        "task_command": "python train_bert_base.py --epochs 5",
        "max_budget_usd": 25.0,
        "estimated_duration_hours": 2.0,
        "preferred_instance_type": "g4dn.xlarge",
        "carbon_weight": 0.5,
        "enable_checkpointing": True,
        "s3_checkpoint_bucket": "greenspot-checkpoints-prod"
    }

    # Dispatch with simulate_preemption=True to trigger the fault scenario
    response = client.post("/api/dispatch?simulate_preemption=true", json=payload)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    
    receipt = response.json()
    
    # Assert preemption occurred
    assert receipt["preemptions_handled"] > 0, "No preemptions were handled."
    assert len(receipt["preemption_history"]) > 0, "Preemption history is empty."
    
    # Assert emergency checkpoint flush to S3 occurred
    first_preemption = receipt["preemption_history"][0]
    assert first_preemption["checkpoint_size_mb"] > 0, "Emergency checkpoint flush did not record any size."
    assert first_preemption["sync_duration_seconds"] > 0, "Emergency checkpoint sync duration not recorded."
    
    # Validate the failover to another instance
    assert first_preemption["evicted_instance_id"] != first_preemption["resumed_instance_id"]
    assert "evicted_region" in first_preemption
    assert "resumed_region" in first_preemption
