"""
AWS IMDSv2 Preemption Polling Daemon & Interruption Event Simulator.
Monitors EC2 Spot Interruption notices (2-minute warning) via IMDSv2:
  - Token endpoint: PUT http://169.254.169.254/latest/api/token
  - Action endpoint: GET http://169.254.169.254/latest/meta-data/spot/instance-action
Includes simulated interruption event generator for demos and local testing.
"""

import time
import json
import logging
import threading
from typing import Optional, Dict, Any, Callable, List
from datetime import datetime, timezone, timedelta
import httpx

logger = logging.getLogger(__name__)

DEFAULT_IMDS_ENDPOINT = "http://169.254.169.254"
DEFAULT_TOKEN_TTL_SECONDS = 21600  # 6 hours
DEFAULT_POLL_INTERVAL_SECONDS = 5.0
DEFAULT_REQUEST_TIMEOUT = 2.0


class IMDSv2Client:
    """
    AWS Instance Metadata Service Version 2 (IMDSv2) client.
    Handles secure session token retrieval and spot interruption notice queries.
    """
    def __init__(
        self,
        base_url: str = DEFAULT_IMDS_ENDPOINT,
        token_ttl_seconds: int = DEFAULT_TOKEN_TTL_SECONDS,
        timeout: float = DEFAULT_REQUEST_TIMEOUT,
        transport: Optional[httpx.BaseTransport] = None
    ):
        self.base_url = base_url.rstrip("/")
        self.token_ttl_seconds = token_ttl_seconds
        self.timeout = timeout
        self._token: Optional[str] = None
        self._token_expiry: float = 0.0
        self._lock = threading.Lock()
        self._transport = transport

    def get_token(self, force_refresh: bool = False) -> Optional[str]:
        """
        Retrieves a session token from IMDSv2.
        PUT /latest/api/token with X-aws-ec2-metadata-token-ttl-seconds header.
        Caches the token until 60 seconds before expiration.
        """
        with self._lock:
            now = time.time()
            if not force_refresh and self._token and now < (self._token_expiry - 60):
                return self._token

            token_url = f"{self.base_url}/latest/api/token"
            headers = {"X-aws-ec2-metadata-token-ttl-seconds": str(self.token_ttl_seconds)}
            try:
                with httpx.Client(timeout=self.timeout, transport=self._transport) as client:
                    resp = client.put(token_url, headers=headers)
                    if resp.status_code == 200:
                        self._token = resp.text.strip()
                        self._token_expiry = now + self.token_ttl_seconds
                        logger.debug("Successfully acquired IMDSv2 token")
                        return self._token
                    else:
                        logger.warning("Failed to obtain IMDSv2 token: HTTP %s", resp.status_code)
                        return None
            except Exception as e:
                logger.debug("IMDSv2 token request failed (likely not on EC2): %s", e)
                return None

    def check_spot_interruption(self) -> Optional[Dict[str, Any]]:
        """
        Polls for EC2 spot interruption notice:
        GET /latest/meta-data/spot/instance-action
        Returns dict with action and time if scheduled for eviction, else None.
        If HTTP 404: no interruption scheduled.
        If HTTP 401: token expired, refreshes token and retries once.
        """
        token = self.get_token()
        if not token:
            return None

        action_url = f"{self.base_url}/latest/meta-data/spot/instance-action"
        headers = {"X-aws-ec2-metadata-token": token}
        try:
            with httpx.Client(timeout=self.timeout, transport=self._transport) as client:
                resp = client.get(action_url, headers=headers)
                if resp.status_code == 200:
                    try:
                        data = resp.json()
                    except Exception:
                        data = {"action": "terminate", "raw": resp.text.strip()}
                    logger.warning("[GreenSpot IMDS] ⚠️ Spot Interruption Notice received: %s", data)
                    return data
                elif resp.status_code == 401:
                    # Token expired, refresh once
                    token = self.get_token(force_refresh=True)
                    if token:
                        headers["X-aws-ec2-metadata-token"] = token
                        retry_resp = client.get(action_url, headers=headers)
                        if retry_resp.status_code == 200:
                            try:
                                return retry_resp.json()
                            except Exception:
                                return {"action": "terminate", "raw": retry_resp.text.strip()}
                    return None
                elif resp.status_code == 404:
                    # Normal healthy state: no interruption scheduled
                    return None
                else:
                    logger.debug("IMDS spot check returned status %s", resp.status_code)
                    return None
        except Exception as e:
            logger.debug("IMDS spot interruption check exception: %s", e)
            return None

    def check_rebalance_recommendation(self) -> Optional[Dict[str, Any]]:
        """
        Polls EC2 Instance Rebalance Recommendation:
        GET /latest/meta-data/events/recommendations/rebalance
        Returns dict with noticeTime if issued, else None.
        """
        token = self.get_token()
        if not token:
            return None

        url = f"{self.base_url}/latest/meta-data/events/recommendations/rebalance"
        headers = {"X-aws-ec2-metadata-token": token}
        try:
            with httpx.Client(timeout=self.timeout, transport=self._transport) as client:
                resp = client.get(url, headers=headers)
                if resp.status_code == 200:
                    try:
                        return resp.json()
                    except Exception:
                        return {"noticeTime": resp.text.strip()}
                return None
        except Exception:
            return None


class SpotPreemptionWatcher:
    """
    Background daemon thread polling IMDSv2 for spot preemption notices.
    Notifies registered callbacks upon detecting an eviction warning.
    """
    def __init__(
        self,
        imds_client: Optional[IMDSv2Client] = None,
        poll_interval_seconds: float = DEFAULT_POLL_INTERVAL_SECONDS,
        callbacks: Optional[List[Callable[[Dict[str, Any]], None]]] = None
    ):
        self.imds_client = imds_client or IMDSv2Client()
        self.poll_interval = poll_interval_seconds
        self.callbacks: List[Callable[[Dict[str, Any]], None]] = list(callbacks or [])
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._interruption_event: Optional[Dict[str, Any]] = None

    def add_callback(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """Registers a callback function to be invoked on preemption."""
        if callback not in self.callbacks:
            self.callbacks.append(callback)

    def remove_callback(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """Removes a registered callback function."""
        if callback in self.callbacks:
            self.callbacks.remove(callback)

    @property
    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    @property
    def interruption_detected(self) -> bool:
        return self._interruption_event is not None

    @property
    def last_event(self) -> Optional[Dict[str, Any]]:
        return self._interruption_event

    def start(self) -> None:
        """Starts the polling daemon thread."""
        if self.is_running:
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run_loop, name="SpotPreemptionWatcher", daemon=True)
        self._thread.start()
        logger.info("SpotPreemptionWatcher daemon started (interval: %.1fs)", self.poll_interval)

    def stop(self, timeout: float = 2.0) -> None:
        """Stops the polling daemon thread."""
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=timeout)
        self._thread = None
        logger.info("SpotPreemptionWatcher daemon stopped")

    def poll_once(self) -> Optional[Dict[str, Any]]:
        """Checks for spot interruption once and triggers callbacks if found."""
        notice = self.imds_client.check_spot_interruption()
        if notice:
            self._trigger_event(notice)
        return notice

    def _trigger_event(self, notice: Dict[str, Any]) -> None:
        self._interruption_event = notice
        for cb in list(self.callbacks):
            try:
                cb(notice)
            except Exception as e:
                logger.error("Error executing preemption callback: %s", e)

    def _run_loop(self) -> None:
        while not self._stop_event.is_set():
            notice = self.poll_once()
            if notice:
                # Stop polling once interruption has been detected
                break
            self._stop_event.wait(self.poll_interval)


# ==============================================================================
# Simulated Interruption Event Generator (Demos & Local Testing)
# ==============================================================================

def create_simulated_interruption(
    action: str = "terminate",
    notice_minutes: int = 2
) -> Dict[str, Any]:
    """
    Generates a realistic AWS IMDSv2 spot interruption notice dictionary.
    Action is typically 'terminate', 'stop', or 'hibernate'.
    Time is set to ISO-8601 UTC timestamp N minutes in the future.
    """
    eviction_time = datetime.now(timezone.utc) + timedelta(minutes=notice_minutes)
    return {
        "action": action,
        "time": eviction_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "simulated": True
    }


class SimulatedInterruptionGenerator:
    """
    Generator for simulating spot preemption events for demos, unit tests, and local resilience runs.
    """
    def __init__(self, watcher: Optional[SpotPreemptionWatcher] = None):
        self.watcher = watcher
        self._timer: Optional[threading.Timer] = None

    def trigger_now(
        self,
        action: str = "terminate",
        notice_minutes: int = 2,
        extra_info: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Immediately generates and emits a simulated interruption notice."""
        event = create_simulated_interruption(action=action, notice_minutes=notice_minutes)
        if extra_info:
            event.update(extra_info)
        logger.warning("[GreenSpot SIMULATOR] ⚠️ Simulated Spot Interruption triggered: %s", event)
        if self.watcher:
            self.watcher._trigger_event(event)
        return event

    def schedule_interruption(
        self,
        delay_seconds: float,
        action: str = "terminate",
        notice_minutes: int = 2,
        callback: Optional[Callable[[Dict[str, Any]], None]] = None
    ) -> threading.Timer:
        """Schedules a simulated spot interruption event after delay_seconds."""
        def _fire():
            event = self.trigger_now(action=action, notice_minutes=notice_minutes)
            if callback:
                callback(event)

        self._timer = threading.Timer(delay_seconds, _fire)
        self._timer.daemon = True
        self._timer.start()
        logger.info("[GreenSpot SIMULATOR] Scheduled simulated interruption in %.1fs", delay_seconds)
        return self._timer

    def cancel(self) -> None:
        """Cancels scheduled simulated interruption if pending."""
        if self._timer and self._timer.is_alive():
            self._timer.cancel()


def simulate_interruption(
    delay_seconds: float = 0.0,
    action: str = "terminate",
    notice_minutes: int = 2,
    watcher: Optional[SpotPreemptionWatcher] = None,
    callback: Optional[Callable[[Dict[str, Any]], None]] = None
) -> Dict[str, Any]:
    """
    Helper function to trigger or schedule a simulated spot preemption interruption.
    """
    gen = SimulatedInterruptionGenerator(watcher=watcher)
    if delay_seconds <= 0:
        event = gen.trigger_now(action=action, notice_minutes=notice_minutes)
        if callback:
            callback(event)
        return event
    else:
        gen.schedule_interruption(
            delay_seconds=delay_seconds,
            action=action,
            notice_minutes=notice_minutes,
            callback=callback
        )
        return create_simulated_interruption(action=action, notice_minutes=notice_minutes)
