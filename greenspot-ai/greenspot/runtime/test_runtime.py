"""
Unit Tests for GreenSpot Runtime Resilience Layer.
Tests:
1. IMDSv2 token acquisition, expiration, retry, and spot interruption notice queries.
2. SpotPreemptionWatcher background polling daemon and callback dispatch.
3. SimulatedInterruptionGenerator and simulated preemption events.
4. S3 multipart upload chunking, error abortion, and local disk fallback.
5. CheckpointManager regular checkpoints and emergency flushes.
6. @checkpoint_protect decorator on training loops, generators, and preemption interruption.
"""

import os
import time
import signal
import shutil
import tempfile
import threading
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

import pytest
import httpx

from greenspot.runtime.preemption import (
    IMDSv2Client,
    SpotPreemptionWatcher,
    SimulatedInterruptionGenerator,
    create_simulated_interruption,
    simulate_interruption,
)
from greenspot.runtime.checkpoint import (
    CheckpointManager,
    S3Uploader,
    CheckpointContext,
    checkpoint_protect,
    PreemptionInterrupted,
    serialize_checkpoint_payload,
)


# ==============================================================================
# Mock Helpers
# ==============================================================================

class MockIMDSHandler:
    """Simulates AWS EC2 IMDSv2 endpoints."""
    def __init__(self):
        self.token = "mock-token-xyz-12345"
        self.interruption_active = False
        self.interruption_action = "terminate"
        self.rebalance_active = False
        self.token_requests = 0
        self.spot_requests = 0

    def handle(self, request: httpx.Request) -> httpx.Response:
        url_path = request.url.path
        if request.method == "PUT" and url_path == "/latest/api/token":
            self.token_requests += 1
            ttl = request.headers.get("X-aws-ec2-metadata-token-ttl-seconds")
            if ttl:
                return httpx.Response(200, text=self.token)
            return httpx.Response(400, text="Missing TTL header")

        elif request.method == "GET" and url_path == "/latest/meta-data/spot/instance-action":
            self.spot_requests += 1
            auth_token = request.headers.get("X-aws-ec2-metadata-token")
            if auth_token != self.token:
                return httpx.Response(401, text="Unauthorized token")

            if self.interruption_active:
                payload = {
                    "action": self.interruption_action,
                    "time": datetime.now(timezone.utc).isoformat()
                }
                return httpx.Response(200, json=payload)
            return httpx.Response(404, text="No spot interruption scheduled")

        elif request.method == "GET" and url_path == "/latest/meta-data/events/recommendations/rebalance":
            auth_token = request.headers.get("X-aws-ec2-metadata-token")
            if auth_token != self.token:
                return httpx.Response(401, text="Unauthorized token")
            if self.rebalance_active:
                return httpx.Response(200, json={"noticeTime": datetime.now(timezone.utc).isoformat()})
            return httpx.Response(404, text="No rebalance recommendation")

        return httpx.Response(404, text="Not Found")


class MockS3Client:
    """Simulates AWS S3 client multipart upload workflow."""
    def __init__(self, should_fail_create: bool = False, fail_part_number: Optional[int] = None):
        self.should_fail_create = should_fail_create
        self.fail_part_number = fail_part_number
        self.uploads: Dict[str, Dict[str, Any]] = {}
        self.completed_objects: Dict[str, Any] = {}
        self.aborted_uploads: List[str] = []
        self.parts_uploaded: List[Dict[str, Any]] = []

    def create_multipart_upload(self, Bucket: str, Key: str) -> Dict[str, Any]:
        if self.should_fail_create:
            raise Exception("Simulated S3 AccessDenied or Connection Timeout")
        upload_id = f"mp-upload-{len(self.uploads) + 1}"
        self.uploads[upload_id] = {"bucket": Bucket, "key": Key, "parts": {}}
        return {"UploadId": upload_id}

    def upload_part(
        self,
        Bucket: str,
        Key: str,
        PartNumber: int,
        UploadId: str,
        Body: bytes
    ) -> Dict[str, Any]:
        if self.fail_part_number is not None and PartNumber == self.fail_part_number:
            raise Exception(f"Simulated connection reset on part {PartNumber}")
        etag = f'"etag-part-{PartNumber}-{len(Body)}"'
        self.uploads[UploadId]["parts"][PartNumber] = {"etag": etag, "size": len(Body)}
        self.parts_uploaded.append({"part_number": PartNumber, "size": len(Body)})
        return {"ETag": etag}

    def complete_multipart_upload(
        self,
        Bucket: str,
        Key: str,
        UploadId: str,
        MultipartUpload: Dict[str, List[Dict[str, Any]]]
    ) -> Dict[str, Any]:
        parts = MultipartUpload["Parts"]
        self.completed_objects[f"{Bucket}/{Key}"] = {
            "upload_id": UploadId,
            "parts": parts,
            "total_parts": len(parts)
        }
        return {"ETag": '"complete-multipart-etag-xyz"'}

    def abort_multipart_upload(self, Bucket: str, Key: str, UploadId: str) -> Dict[str, Any]:
        self.aborted_uploads.append(UploadId)
        if UploadId in self.uploads:
            del self.uploads[UploadId]
        return {}


# ==============================================================================
# 1. IMDSv2 Client Tests
# ==============================================================================

def test_imdsv2_token_acquisition_and_caching():
    handler = MockIMDSHandler()
    transport = httpx.MockTransport(handler.handle)
    client = IMDSv2Client(base_url="http://169.254.169.254", token_ttl_seconds=3600, transport=transport)

    # Initial token fetch
    token = client.get_token()
    assert token == "mock-token-xyz-12345"
    assert handler.token_requests == 1

    # Second fetch should use cached token
    token2 = client.get_token()
    assert token2 == token
    assert handler.token_requests == 1

    # Force refresh
    token3 = client.get_token(force_refresh=True)
    assert token3 == token
    assert handler.token_requests == 2


def test_imdsv2_spot_interruption_notices():
    handler = MockIMDSHandler()
    transport = httpx.MockTransport(handler.handle)
    client = IMDSv2Client(transport=transport)

    # 1. No interruption scheduled (404)
    handler.interruption_active = False
    notice = client.check_spot_interruption()
    assert notice is None
    assert handler.spot_requests == 1

    # 2. Spot preemption active (200)
    handler.interruption_active = True
    handler.interruption_action = "terminate"
    notice = client.check_spot_interruption()
    assert notice is not None
    assert notice["action"] == "terminate"
    assert "time" in notice
    assert handler.spot_requests == 2


def test_imdsv2_rebalance_recommendation():
    handler = MockIMDSHandler()
    transport = httpx.MockTransport(handler.handle)
    client = IMDSv2Client(transport=transport)

    assert client.check_rebalance_recommendation() is None

    handler.rebalance_active = True
    rebal = client.check_rebalance_recommendation()
    assert rebal is not None
    assert "noticeTime" in rebal


def test_imdsv2_error_handling_outside_ec2():
    # Outside EC2 with unreachable host should gracefully return None without crashing
    client = IMDSv2Client(base_url="http://192.0.2.1:1", timeout=0.1)
    token = client.get_token()
    assert token is None
    notice = client.check_spot_interruption()
    assert notice is None


# ==============================================================================
# 2. SpotPreemptionWatcher Tests
# ==============================================================================

def test_spot_preemption_watcher_background_polling():
    handler = MockIMDSHandler()
    transport = httpx.MockTransport(handler.handle)
    client = IMDSv2Client(transport=transport)

    received_events = []
    watcher = SpotPreemptionWatcher(
        imds_client=client,
        poll_interval_seconds=0.05,
        callbacks=[lambda event: received_events.append(event)]
    )

    watcher.start()
    assert watcher.is_running
    time.sleep(0.1)
    assert len(received_events) == 0
    assert not watcher.interruption_detected

    # Trigger interruption in mock IMDS
    handler.interruption_active = True
    # Wait for daemon poll
    time.sleep(0.15)
    watcher.stop()
    assert not watcher.is_running

    assert len(received_events) >= 1
    assert received_events[0]["action"] == "terminate"
    assert watcher.interruption_detected


# ==============================================================================
# 3. Simulated Interruption Generator Tests
# ==============================================================================

def test_simulated_interruption_generator():
    sim_event = create_simulated_interruption(action="hibernate", notice_minutes=2)
    assert sim_event["action"] == "hibernate"
    assert sim_event["simulated"] is True
    assert "time" in sim_event

    fired_events = []
    watcher = SpotPreemptionWatcher(callbacks=[lambda ev: fired_events.append(ev)])
    generator = SimulatedInterruptionGenerator(watcher=watcher)

    # Immediate trigger
    event = generator.trigger_now(action="stop")
    assert event["action"] == "stop"
    assert len(fired_events) == 1
    assert fired_events[0]["action"] == "stop"

    # Scheduled trigger
    generator.schedule_interruption(delay_seconds=0.05, action="terminate")
    time.sleep(0.1)
    assert len(fired_events) == 2
    assert fired_events[1]["action"] == "terminate"


def test_simulate_interruption_helper():
    res = simulate_interruption(delay_seconds=0.0, action="terminate")
    assert res["action"] == "terminate"
    assert res["simulated"] is True


# ==============================================================================
# 4. S3 Multipart Upload & Local Disk Fallback Tests
# ==============================================================================

def test_s3_multipart_upload_success():
    mock_s3 = MockS3Client()
    # Use 100-byte part size for testing chunking
    uploader = S3Uploader(s3_client=mock_s3, part_size_bytes=100)

    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = os.path.join(tmpdir, "model_weights.bin")
        # 350 bytes -> should create 4 parts (100, 100, 100, 50)
        with open(test_file, "wb") as f:
            f.write(b"x" * 350)

        result = uploader.upload_file(test_file, bucket="my-bucket", key="models/weights.bin")

        assert result["status"] == "uploaded"
        assert result["fallback"] is False
        assert result["parts_count"] == 4
        assert len(mock_s3.parts_uploaded) == 4
        assert "my-bucket/models/weights.bin" in mock_s3.completed_objects
        assert len(mock_s3.aborted_uploads) == 0


def test_s3_multipart_upload_abort_and_fallback_on_failure():
    # Fail during part 2 upload
    mock_s3 = MockS3Client(fail_part_number=2)
    uploader = S3Uploader(s3_client=mock_s3, part_size_bytes=100)

    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = os.path.join(tmpdir, "model_weights.bin")
        with open(test_file, "wb") as f:
            f.write(b"y" * 250)

        result = uploader.upload_file(test_file, bucket="my-bucket", key="models/weights.bin")

        # Must fall back to local disk and abort S3 upload
        assert result["status"] == "fallback_local"
        assert result["fallback"] is True
        assert len(mock_s3.aborted_uploads) == 1
        assert os.path.exists(result["local_path"])
        assert result["hash"] is not None


def test_s3_local_disk_fallback_without_s3_client():
    uploader = S3Uploader(s3_client=None)
    # Monkey-patch get_client to return None
    uploader.get_client = lambda: None

    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = os.path.join(tmpdir, "weights.json")
        with open(test_file, "w") as f:
            f.write('{"epoch": 1, "loss": 0.3}')

        result = uploader.upload_file(test_file, bucket="my-bucket", key="weights.json")

        assert result["status"] == "fallback_local"
        assert result["fallback"] is True
        assert os.path.exists(result["local_path"])
        assert "hash" in result


# ==============================================================================
# 5. CheckpointManager Regular & Emergency Checkpoint Tests
# ==============================================================================

def test_checkpoint_manager_save_and_emergency():
    mock_s3 = MockS3Client()
    uploader = S3Uploader(s3_client=mock_s3, part_size_bytes=1024)

    with tempfile.TemporaryDirectory() as tmpdir:
        mgr = CheckpointManager(
            bucket_name="greenspot-checkpoints-prod",
            local_dir=tmpdir,
            s3_uploader=uploader
        )

        # 1. Regular save_checkpoint
        res = mgr.save_checkpoint(job_id="job-101", step=10, weights_data={"w1": 0.42, "w2": 0.88})
        assert os.path.exists(res["local_path"])
        assert res["s3_uri"] == "s3://greenspot-checkpoints-prod/job-101/job-101_step_10.json"
        assert res["hash"] is not None
        assert res["uploaded_to_s3"] is True

        # 2. Emergency flush
        flush_res = mgr.emergency_flush(
            job_id="job-101",
            state_summary="Preemption notice received",
            state_data={"epoch": 2, "weights": [1, 2, 3]}
        )
        assert flush_res["flushed"] is True
        assert flush_res["duration_seconds"] > 0
        assert flush_res["size_mb"] > 0
        assert os.path.exists(flush_res["local_path"])
        assert flush_res["s3_path"] == "s3://greenspot-checkpoints-prod/job-101/emergency_snapshot.chk"


# ==============================================================================
# 6. @checkpoint_protect Decorator Tests
# ==============================================================================

def test_checkpoint_protect_decorator_with_context():
    mock_s3 = MockS3Client()
    uploader = S3Uploader(s3_client=mock_s3, part_size_bytes=1024)

    with tempfile.TemporaryDirectory() as tmpdir:
        mgr = CheckpointManager(bucket_name="test-bucket", local_dir=tmpdir, s3_uploader=uploader)

        @checkpoint_protect(
            s3_bucket="test-bucket",
            interval_steps=5,
            local_dir=tmpdir,
            checkpoint_manager=mgr,
            job_id="training-run-1"
        )
        def train_loop(ctx: CheckpointContext):
            for step in range(1, 16):
                # Simulated training step
                ctx.step(step, state={"step": step, "loss": 1.0 / step})
            return "COMPLETED"

        result = train_loop()
        assert result == "COMPLETED"

        # Steps 5, 10, 15 should have triggered checkpoint saves
        saved_files = os.listdir(tmpdir)
        checkpoint_files = [f for f in saved_files if f.endswith(".json")]
        assert len(checkpoint_files) == 3
        assert "training-run-1_step_5.json" in checkpoint_files
        assert "training-run-1_step_10.json" in checkpoint_files
        assert "training-run-1_step_15.json" in checkpoint_files


def test_checkpoint_protect_generator_support():
    mock_s3 = MockS3Client()
    uploader = S3Uploader(s3_client=mock_s3, part_size_bytes=1024)

    with tempfile.TemporaryDirectory() as tmpdir:
        mgr = CheckpointManager(bucket_name="test-bucket", local_dir=tmpdir, s3_uploader=uploader)

        @checkpoint_protect(
            s3_bucket="test-bucket",
            interval_steps=3,
            local_dir=tmpdir,
            checkpoint_manager=mgr,
            job_id="gen-job"
        )
        def train_generator():
            for i in range(1, 10):
                yield i, {"layer1": i * 0.1}

        collected = list(train_generator())
        assert len(collected) == 9

        saved_files = [f for f in os.listdir(tmpdir) if f.endswith(".json")]
        # Steps 3, 6, 9
        assert len(saved_files) == 3


def test_checkpoint_protect_intercepts_preemption():
    mock_s3 = MockS3Client()
    uploader = S3Uploader(s3_client=mock_s3, part_size_bytes=1024)

    with tempfile.TemporaryDirectory() as tmpdir:
        mgr = CheckpointManager(bucket_name="test-bucket", local_dir=tmpdir, s3_uploader=uploader)
        watcher = SpotPreemptionWatcher()

        @checkpoint_protect(
            s3_bucket="test-bucket",
            interval_steps=100,
            local_dir=tmpdir,
            checkpoint_manager=mgr,
            watcher=watcher,
            job_id="preempted-job"
        )
        def training_with_eviction(ctx: CheckpointContext):
            for step in range(1, 50):
                ctx.step(step, state={"step": step, "weights": [0.1, 0.2]})
                if step == 10:
                    # Simulate spot preemption notice arriving from AWS IMDS
                    simulate_interruption(watcher=watcher, action="terminate")

        with pytest.raises(PreemptionInterrupted) as exc_info:
            training_with_eviction()

        assert "Preemption occurred" in str(exc_info.value)
        # Emergency snapshot must be present locally and synced
        emergency_files = [f for f in os.listdir(tmpdir) if "emergency_snapshot" in f]
        assert len(emergency_files) == 1
        assert exc_info.value.checkpoint_info["flushed"] is True


def test_checkpoint_protect_sigterm_handling():
    mock_s3 = MockS3Client()
    uploader = S3Uploader(s3_client=mock_s3, part_size_bytes=1024)

    with tempfile.TemporaryDirectory() as tmpdir:
        mgr = CheckpointManager(bucket_name="test-bucket", local_dir=tmpdir, s3_uploader=uploader)

        @checkpoint_protect(
            s3_bucket="test-bucket",
            interval_steps=100,
            local_dir=tmpdir,
            checkpoint_manager=mgr,
            job_id="sigterm-job"
        )
        def training_sigterm(ctx: CheckpointContext):
            for step in range(1, 20):
                ctx.step(step, state={"epoch": step})
                if step == 5:
                    # Simulate receiving SIGTERM from OS / hypervisor
                    os.kill(os.getpid(), signal.SIGTERM)

        with pytest.raises(PreemptionInterrupted) as exc_info:
            training_sigterm()

        assert "SIGTERM" in str(exc_info.value)
        emergency_files = [f for f in os.listdir(tmpdir) if "emergency_snapshot" in f]
        assert len(emergency_files) == 1
