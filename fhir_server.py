"""
Lightweight FHIR R4 server (in-memory) using Flask.
Implements the FHIR REST API subset needed for the NHS mental health demo:
  GET  /fhir/metadata
  POST /fhir/<ResourceType>
  GET  /fhir/<ResourceType>/<id>
  PUT  /fhir/<ResourceType>/<id>
  GET  /fhir/<ResourceType>?<search params>
  GET  /fhir/Patient/<id>/$everything
  POST /fhir/  (transaction bundle)
"""
import uuid
import json
from datetime import datetime, timezone
from flask import Flask, request, jsonify, Response

app = Flask(__name__)

# In-memory store: {resource_type: {id: resource_dict}}
store: dict[str, dict[str, dict]] = {}

FHIR_JSON = "application/fhir+json"
SUPPORTED = [
    "Patient", "Practitioner", "Organization",
    "Condition", "Observation", "MedicationRequest", "Encounter",
]


def now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def store_resource(resource: dict) -> dict:
    rtype = resource["resourceType"]
    rid = resource.get("id") or str(uuid.uuid4())
    resource["id"] = rid
    resource.setdefault("meta", {})["lastUpdated"] = now_iso()
    resource["meta"]["versionId"] = "1"
    store.setdefault(rtype, {})[rid] = resource
    return resource


def bundle(entries: list, search_mode="match") -> dict:
    return {
        "resourceType": "Bundle",
        "type": "searchset",
        "total": len(entries),
        "entry": [
            {
                "fullUrl": f"http://localhost:8080/fhir/{e['resourceType']}/{e['id']}",
                "resource": e,
                "search": {"mode": search_mode},
            }
            for e in entries
        ],
    }


def operation_outcome(severity, code, diagnostics) -> dict:
    return {
        "resourceType": "OperationOutcome",
        "issue": [{"severity": severity, "code": code, "diagnostics": diagnostics}],
    }


def fhir_response(data, status=200):
    return Response(
        json.dumps(data, default=str),
        status=status,
        mimetype=FHIR_JSON,
    )


# ── Capability Statement ─────────────────────────────────────────────────────
@app.route("/fhir/metadata", methods=["GET"])
def metadata():
    cs = {
        "resourceType": "CapabilityStatement",
        "status": "active",
        "date": "2026-04-22",
        "kind": "instance",
        "fhirVersion": "4.0.1",
        "format": ["application/fhir+json"],
        "software": {
            "name": "NHS Mental Health FHIR Server (Python/Flask)",
            "version": "1.0.0",
        },
        "rest": [
            {
                "mode": "server",
                "resource": [
                    {
                        "type": rt,
                        "interaction": [
                            {"code": "read"},
                            {"code": "create"},
                            {"code": "update"},
                            {"code": "search-type"},
                        ],
                    }
                    for rt in SUPPORTED
                ],
            }
        ],
    }
    return fhir_response(cs)


# ── Create resource ───────────────────────────────────────────────────────────
@app.route("/fhir/<resource_type>", methods=["POST"])
def create(resource_type):
    if resource_type not in SUPPORTED:
        return fhir_response(
            operation_outcome("error", "not-supported", f"Resource type {resource_type} not supported"),
            status=400,
        )
    resource = request.get_json(force=True)
    if not resource or resource.get("resourceType") != resource_type:
        return fhir_response(
            operation_outcome("error", "invalid", "Invalid resource body"), status=400
        )
    saved = store_resource(resource)
    resp = fhir_response(saved, status=201)
    resp.headers["Location"] = (
        f"http://localhost:8080/fhir/{resource_type}/{saved['id']}/_history/1"
    )
    return resp


# ── Read resource ─────────────────────────────────────────────────────────────
@app.route("/fhir/<resource_type>/<rid>", methods=["GET"])
def read(resource_type, rid):
    # Handle $everything operation
    if rid.startswith("$"):
        return globals()[f"op_{rid.lstrip('$')}"](resource_type)
    res = store.get(resource_type, {}).get(rid)
    if not res:
        return fhir_response(
            operation_outcome("error", "not-found", f"{resource_type}/{rid} not found"),
            status=404,
        )
    return fhir_response(res)


@app.route("/fhir/<resource_type>/<rid>/$everything", methods=["GET"])
def patient_everything(resource_type, rid):
    if resource_type != "Patient":
        return fhir_response(
            operation_outcome("error", "not-supported", "$everything only supported for Patient"),
            status=400,
        )
    patient = store.get("Patient", {}).get(rid)
    if not patient:
        return fhir_response(
            operation_outcome("error", "not-found", f"Patient/{rid} not found"), status=404
        )
    patient_ref = f"Patient/{rid}"
    results = [patient]
    for rtype in ["Condition", "Observation", "MedicationRequest", "Encounter"]:
        for res in store.get(rtype, {}).values():
            subj = res.get("subject", {}).get("reference", "")
            if subj == patient_ref:
                results.append(res)
    b = bundle(results)
    b["type"] = "searchset"
    return fhir_response(b)


# ── Update resource ───────────────────────────────────────────────────────────
@app.route("/fhir/<resource_type>/<rid>", methods=["PUT"])
def update(resource_type, rid):
    resource = request.get_json(force=True)
    if not resource or resource.get("resourceType") != resource_type:
        return fhir_response(
            operation_outcome("error", "invalid", "Invalid resource body"), status=400
        )
    resource["id"] = rid
    saved = store_resource(resource)
    return fhir_response(saved)


# ── Search ────────────────────────────────────────────────────────────────────
@app.route("/fhir/<resource_type>", methods=["GET"])
def search(resource_type):
    params = dict(request.args)
    resources = list(store.get(resource_type, {}).values())
    results = []

    for res in resources:
        match = True
        for key, val in params.items():
            if key == "identifier":
                # Match system|value or just value
                found = False
                for ident in res.get("identifier", []):
                    sys_val = f"{ident.get('system','')}|{ident.get('value','')}"
                    if val in (ident.get("value", ""), sys_val):
                        found = True
                        break
                if not found:
                    match = False
            elif key == "patient":
                subj = (
                    res.get("subject", {}).get("reference", "")
                    or res.get("patient", {}).get("reference", "")
                )
                if not (subj == f"Patient/{val}" or subj.endswith(f"/{val}")):
                    match = False
            elif key == "clinical-status":
                cs = res.get("clinicalStatus", {})
                codes = [c.get("code") for c in cs.get("coding", [])]
                if val not in codes:
                    match = False
            elif key == "status":
                if res.get("status") != val:
                    match = False
            elif key == "category":
                cats = res.get("category", [])
                found = any(
                    val in [c.get("code") for c in cat.get("coding", [])]
                    for cat in cats
                )
                if not found:
                    match = False
        if match:
            results.append(res)

    return fhir_response(bundle(results))


# ── Transaction Bundle ────────────────────────────────────────────────────────
@app.route("/fhir/", methods=["POST"])
@app.route("/fhir", methods=["POST"])
def transaction():
    body = request.get_json(force=True)
    if not body or body.get("resourceType") != "Bundle":
        return fhir_response(
            operation_outcome("error", "invalid", "Expected a Bundle resource"), status=400
        )

    bundle_type = body.get("type", "")
    if bundle_type not in ("transaction", "batch"):
        return fhir_response(
            operation_outcome("error", "invalid", f"Unsupported bundle type: {bundle_type}"),
            status=400,
        )

    # Map urn:uuid references so cross-entry refs resolve correctly
    urn_map: dict[str, str] = {}
    response_entries = []

    for entry in body.get("entry", []):
        resource = entry.get("resource", {})
        req = entry.get("request", {})
        method = req.get("method", "POST")
        full_url = entry.get("fullUrl", "")

        if method == "POST":
            saved = store_resource(resource)
            if full_url.startswith("urn:uuid:"):
                urn_map[full_url] = f"{saved['resourceType']}/{saved['id']}"
            response_entries.append(
                {
                    "fullUrl": f"http://localhost:8080/fhir/{saved['resourceType']}/{saved['id']}",
                    "resource": saved,
                    "response": {
                        "status": "201 Created",
                        "location": f"{saved['resourceType']}/{saved['id']}/_history/1",
                        "lastModified": now_iso(),
                    },
                }
            )

    # Resolve urn references in saved resources
    for entry in response_entries:
        res = entry["resource"]
        for field in ("subject", "recorder", "requester", "serviceProvider"):
            if field in res:
                ref = res[field].get("reference", "")
                if ref in urn_map:
                    res[field]["reference"] = urn_map[ref]

    response_bundle = {
        "resourceType": "Bundle",
        "type": "transaction-response",
        "entry": response_entries,
    }
    return fhir_response(response_bundle, status=200)


if __name__ == "__main__":
    print("Starting NHS Mental Health FHIR R4 server on http://localhost:8080")
    print("Endpoint: http://localhost:8080/fhir")
    app.run(host="0.0.0.0", port=8080, debug=False)
