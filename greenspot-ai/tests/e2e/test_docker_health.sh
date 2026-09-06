#!/bin/bash

echo "Starting docker containers..."
docker-compose up -d

echo "Waiting for 5 seconds..."
sleep 5

echo "Testing /api/stats endpoint..."
STATUS_CODE=$(curl -o /dev/null -s -w "%{http_code}\n" http://localhost:8000/api/stats)

if [ "$STATUS_CODE" -eq 200 ]; then
    echo "Success: Received 200 OK"
    EXIT_CODE=0
else
    echo "Error: Expected 200 OK, got $STATUS_CODE"
    EXIT_CODE=1
fi

echo "Tearing down docker containers..."
docker-compose down

exit $EXIT_CODE
