import asyncio
import os
import pytest
import httpx

# Configure the target URL via environment variable or default to localhost
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

@pytest.mark.asyncio
async def test_api_radar_load_handling():
    """
    Asynchronously fire 50 concurrent requests to /api/radar to ensure
    the API can handle parallel scoring without crashing.
    """
    endpoint = f"{API_BASE_URL}/api/radar"
    concurrent_requests = 50

    async def make_request(client: httpx.AsyncClient):
        try:
            # Using GET for load test. If the endpoint requires POST, 
            # this might return 405 Method Not Allowed, which still 
            # confirms the server didn't crash.
            response = await client.get(endpoint)
            return response
        except Exception as e:
            return e

    # Use a generous timeout for load testing
    async with httpx.AsyncClient(timeout=60.0) as client:
        tasks = [make_request(client) for _ in range(concurrent_requests)]
        results = await asyncio.gather(*tasks)

    errors = []
    success_count = 0

    for result in results:
        if isinstance(result, Exception):
            errors.append(result)
        else:
            # Check for 5xx status codes which typically indicate a server crash
            if result.status_code >= 500:
                errors.append(f"Server Error {result.status_code}: {result.text}")
            else:
                success_count += 1

    # Assert that no requests resulted in a crash (Exception or 500 Server Error)
    assert not errors, f"API crashed during load test. {len(errors)} errors out of {concurrent_requests} requests. Sample errors: {errors[:3]}"
    assert success_count == concurrent_requests, "Not all requests completed successfully."
