import pytest
import asyncio
from starlette.testclient import TestClient

from greenspot.core.scorer import ArbitrageScorer
from greenspot.runtime.launcher import WorkloadLauncher
from greenspot.schemas import JobSubmission
from greenspot.receipt.generator import render_html_receipt, ReceiptFormatter
from greenspot.api.server import app, JOB_HISTORY


client = TestClient(app)


def test_scorer_ranking():
    scorer = ArbitrageScorer()
    candidates = asyncio.run(scorer.rank_candidates(instance_type="g4dn.xlarge", carbon_weight=0.5))
    assert len(candidates) > 0
    # Rank 1 should have lower composite score than Rank 2
    assert candidates[0].composite_score <= candidates[1].composite_score
    # eu-north-1 or ca-central-1 should be at the top due to clean hydro/nuclear energy
    top_regions = [c.region_id for c in candidates[:3]]
    assert "eu-north-1" in top_regions or "ca-central-1" in top_regions


def test_execution_and_preemption():
    scorer = ArbitrageScorer()
    launcher = WorkloadLauncher()
    candidates = asyncio.run(scorer.rank_candidates(instance_type="g4dn.xlarge", carbon_weight=0.5))
    
    submission = JobSubmission(
        task_command="python test_model.py",
        max_budget_usd=10.0,
        estimated_duration_hours=1.0
    )
    receipt = asyncio.run(launcher.execute_job(submission, candidates, simulate_preemption=True))
    assert receipt.status.value == "completed"
    assert receipt.savings_percentage > 40.0
    assert receipt.preemptions_handled == 1
    assert len(receipt.preemption_history) == 1


def test_html_receipt_generation():
    scorer = ArbitrageScorer()
    launcher = WorkloadLauncher()
    candidates = asyncio.run(scorer.rank_candidates(instance_type="g4dn.xlarge", carbon_weight=0.5))
    
    submission = JobSubmission(
        task_command="python train_eval.py",
        max_budget_usd=15.0,
        estimated_duration_hours=1.5
    )
    receipt = asyncio.run(launcher.execute_job(submission, candidates, simulate_preemption=False))
    
    # Test class method
    html_out = ReceiptFormatter.render_html_receipt(receipt)
    assert "<!DOCTYPE html>" in html_out
    assert receipt.job_id in html_out
    assert "Certified FinOps" in html_out
    assert f"${receipt.total_savings_usd:.2f}" in html_out
    assert f"{receipt.carbon_avoided_gco2:.1f}" in html_out
    assert "window.print()" in html_out

    # Test standalone module function
    html_out2 = render_html_receipt(receipt)
    assert html_out2 == html_out


def test_api_history_and_stats():
    # Test history endpoint
    resp_hist = client.get("/api/history")
    assert resp_hist.status_code == 200
    history = resp_hist.json()
    assert isinstance(history, list)
    assert len(history) >= 1
    first_job = history[0]
    assert "job_id" in first_job
    assert "actual_spot_cost_usd" in first_job
    assert "carbon_avoided_gco2" in first_job

    # Test stats endpoint
    resp_stats = client.get("/api/stats")
    assert resp_stats.status_code == 200
    stats = resp_stats.json()
    assert "total_carbon_avoided_gco2" in stats
    assert "total_cost_saved_usd" in stats
    assert "average_clean_energy_pct" in stats
    assert stats["total_cost_saved_usd"] > 0
    assert stats["total_jobs_executed"] == len(history)


def test_api_dashboard_html():
    resp_dash = client.get("/dashboard")
    assert resp_dash.status_code == 200
    assert "text/html" in resp_dash.headers["content-type"]
    content = resp_dash.text
    assert "GreenSpot" in content
    assert "Arbitrage Radar" in content
    assert "Dispatch Workload" in content
    assert "alpinejs" in content
    assert "tailwindcss" in content

    # Test root redirect
    resp_root = client.get("/", follow_redirects=False)
    assert resp_root.status_code in [307, 302]
    assert resp_root.headers["location"] == "/dashboard"


def test_api_receipt_endpoints():
    history = client.get("/api/history").json()
    target_job = history[0]
    job_id = target_job["job_id"]

    # Test JSON receipt endpoint
    resp_json = client.get(f"/api/receipt/{job_id}")
    assert resp_json.status_code == 200
    assert resp_json.json()["job_id"] == job_id

    # Test HTML receipt endpoint
    resp_html = client.get(f"/api/receipt/{job_id}/html")
    assert resp_html.status_code == 200
    assert "text/html" in resp_html.headers["content-type"]
    assert job_id in resp_html.text
    assert "Scope 2/3 Clean Energy & Arbitrage Receipt" in resp_html.text

    # Test 404 for unknown job
    resp_404 = client.get("/api/receipt/job-nonexistent")
    assert resp_404.status_code == 404


def test_api_dispatch_updates_ledger_and_stats():
    initial_stats = client.get("/api/stats").json()
    initial_count = initial_stats["total_jobs_executed"]
    initial_savings = initial_stats["total_cost_saved_usd"]

    payload = {
        "task_command": "python test_dispatch_api.py",
        "preferred_instance_type": "g4dn.xlarge",
        "estimated_duration_hours": 1.0,
        "max_budget_usd": 20.0,
        "carbon_weight": 0.7,
        "enable_checkpointing": True
    }
    resp = client.post("/api/dispatch?simulate_preemption=true", json=payload)
    assert resp.status_code == 200
    receipt = resp.json()
    assert receipt["task_command"] == payload["task_command"]
    assert receipt["savings_percentage"] > 0

    # History should contain the new job at index 0
    new_history = client.get("/api/history").json()
    assert len(new_history) == initial_count + 1
    assert new_history[0]["job_id"] == receipt["job_id"]

    # Stats should reflect updated numbers
    updated_stats = client.get("/api/stats").json()
    assert updated_stats["total_jobs_executed"] == initial_count + 1
    assert updated_stats["total_cost_saved_usd"] > initial_savings
