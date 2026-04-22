#!/usr/bin/env bash
# NHS Severe Mental Health — HAPI FHIR full-stack demo launcher
set -euo pipefail

FHIR_BASE="http://localhost:8080/fhir"
MAX_WAIT=180   # seconds before giving up

echo "======================================================================="
echo "  NHS Severe Mental Health — HAPI FHIR Full-Stack Demo"
echo "======================================================================="

# ── Start Docker stack ──────────────────────────────────────────────────────
echo ""
echo "Step 1/3  Starting HAPI FHIR server (Docker Compose)..."
docker-compose up -d

# ── Wait for FHIR server to be healthy ─────────────────────────────────────
echo ""
echo "Step 2/3  Waiting for HAPI FHIR server to be ready..."
WAITED=0
until curl -sf "${FHIR_BASE}/metadata" -o /dev/null; do
    if [ "$WAITED" -ge "$MAX_WAIT" ]; then
        echo ""
        echo "ERROR: Server did not become ready within ${MAX_WAIT}s"
        echo "       Check logs:  docker-compose logs hapi-fhir"
        exit 1
    fi
    printf "."
    sleep 5
    WAITED=$((WAITED + 5))
done
echo ""
echo "HAPI FHIR server is ready at ${FHIR_BASE}"

# ── Run Python demo ─────────────────────────────────────────────────────────
echo ""
echo "Step 3/3  Running FHIR REST API demo (15 calls)..."
pip install -q -r requirements.txt
python fhir_api_demo.py

echo ""
echo "To stop the server:  docker-compose down"
echo "To view the UI:      http://localhost:8080"
