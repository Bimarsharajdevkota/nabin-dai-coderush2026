import httpx
import os
import pytest

def test_api_workflow():
    """
    Test the full E2E flow: POST to /api/dispatch, extract the job_id from the receipt,
    and then GET /api/history to ensure the receipt was properly recorded.
    """
    base_url = os.getenv("BASE_URL", "http://localhost:8000")
    
    # 1. POST to /api/dispatch
    dispatch_payload = {
        "task_command": "echo 'Testing API Workflow'",
        "max_budget_usd": 15.0,
        "estimated_duration_hours": 1.0,
        "preferred_instance_type": "g4dn.xlarge",
        "carbon_weight": 0.5,
        "enable_checkpointing": True,
    }
    
    dispatch_response = httpx.post(
        f"{base_url}/api/dispatch",
        params={"simulate_preemption": "false"},
        json=dispatch_payload
    )
    
    assert dispatch_response.status_code == 200, f"Dispatch failed: {dispatch_response.text}"
    
    receipt = dispatch_response.json()
    job_id = receipt.get("job_id")
    assert job_id is not None, "job_id missing from receipt"
    
    # 2. GET /api/history
    history_response = httpx.get(f"{base_url}/api/history")
    assert history_response.status_code == 200, f"History fetch failed: {history_response.text}"
    
    history = history_response.json()
    assert isinstance(history, list), "Expected history to be a list"
    
    # 3. Verify job_id is in history
    recorded_job_ids = [job.get("job_id") for job in history]
    assert job_id in recorded_job_ids, f"job_id {job_id} not found in history"
