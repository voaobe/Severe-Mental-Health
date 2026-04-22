"""
NHS Severe Mental Health - HAPI FHIR Server REST API Demo
Makes 15 REST API calls demonstrating FHIR R4 CRUD operations
against a live HAPI FHIR test server.
"""
import json
import sys
import requests

from generate_nhs_data import (
    generate_condition,
    generate_encounter,
    generate_gaf_observation,
    generate_medication_request,
    generate_nhs_number,
    generate_organization,
    generate_patient,
    generate_practitioner,
)

FHIR_BASE = "http://localhost:8080/fhir"
HEADERS = {
    "Content-Type": "application/fhir+json",
    "Accept": "application/fhir+json",
}

_call_count = 0


def print_call(method, endpoint, description, response):
    global _call_count
    _call_count += 1
    ok = response.status_code < 400
    icon = "[OK]" if ok else "[ERR]"
    print(f"\n{'─'*70}")
    print(f"  Call #{_call_count:02d} | {description}")
    print(f"  {method} {FHIR_BASE}{endpoint}")
    print(f"  {icon} HTTP {response.status_code} {response.reason}")
    try:
        body = response.json()
        rtype = body.get("resourceType", "")
        if rtype == "Bundle":
            total = body.get("total", len(body.get("entry", [])))
            entries = body.get("entry", [])
            print(f"  Bundle total: {total} resource(s)")
            for e in entries[:4]:
                r = e.get("resource", {})
                print(f"    • {r.get('resourceType','?')}/{r.get('id','?')}")
            if len(entries) > 4:
                print(f"    … and {len(entries)-4} more")
        elif rtype == "OperationOutcome":
            for issue in body.get("issue", []):
                sev = issue.get("severity", "?")
                msg = issue.get("diagnostics") or issue.get("details", {}).get("text", "")
                print(f"  OperationOutcome [{sev}]: {msg[:120]}")
        elif rtype:
            rid = body.get("id", "?")
            print(f"  Resource: {rtype}/{rid}")
            if rtype == "Patient":
                name = body.get("name", [{}])[0]
                given = " ".join(name.get("given", []))
                family = name.get("family", "")
                dob = body.get("birthDate", "")
                print(f"  Patient: {given} {family}, DOB: {dob}")
            elif rtype == "Condition":
                code_text = body.get("code", {}).get("text", "")
                print(f"  Condition: {code_text}")
            elif rtype == "MedicationRequest":
                med = body.get("medicationCodeableConcept", {}).get("text", "")
                print(f"  Medication: {med}")
            elif rtype == "Observation":
                val = body.get("valueQuantity", {})
                print(f"  Value: {val.get('value')} {val.get('unit','')}")
    except Exception:
        print(f"  Body: {response.text[:200]}")


def extract_id(response):
    data = response.json()
    if "id" in data:
        return data["id"]
    loc = response.headers.get("Location", "")
    parts = loc.rstrip("/").split("/")
    if "_history" in parts:
        idx = parts.index("_history")
        return parts[idx - 1]
    return parts[-1] if parts else "unknown"


def check_server():
    print(f"Connecting to HAPI FHIR server at {FHIR_BASE} ...")
    try:
        r = requests.get(f"{FHIR_BASE}/metadata", headers=HEADERS, timeout=15)
        r.raise_for_status()
        meta = r.json()
        sw = meta.get("software", {})
        print(f"Connected: {sw.get('name','HAPI FHIR')} v{sw.get('version','?')}")
        print(f"FHIR version: {meta.get('fhirVersion','R4')}")
        return True
    except requests.exceptions.ConnectionError:
        print("ERROR: Cannot connect to FHIR server.")
        print("       Run:  docker-compose up -d")
        print("       Then wait ~60 s and retry.")
        return False
    except Exception as exc:
        print(f"ERROR: {exc}")
        return False


def run():
    print("=" * 70)
    print("  NHS Severe Mental Health — HAPI FHIR R4 REST API Demo")
    print("=" * 70)

    if not check_server():
        sys.exit(1)

    # ── Generate in-memory NHS data ──────────────────────────────────────────
    org_resource = generate_organization()
    prac_resource = generate_practitioner()
    nhs_number = generate_nhs_number()
    patient_resource = generate_patient(nhs_number)

    # ── CALL 1: Create NHS Trust Organisation ────────────────────────────────
    r = requests.post(f"{FHIR_BASE}/Organization", headers=HEADERS,
                      json=org_resource, timeout=30)
    print_call("POST", "/Organization", "Create NHS Trust Organisation", r)
    org_id = extract_id(r)
    org_ref = f"Organization/{org_id}"

    # ── CALL 2: Create Consultant Psychiatrist ───────────────────────────────
    r = requests.post(f"{FHIR_BASE}/Practitioner", headers=HEADERS,
                      json=prac_resource, timeout=30)
    print_call("POST", "/Practitioner", "Create Consultant Psychiatrist", r)
    prac_id = extract_id(r)
    prac_ref = f"Practitioner/{prac_id}"

    # ── CALL 3: Create NHS Patient ───────────────────────────────────────────
    r = requests.post(f"{FHIR_BASE}/Patient", headers=HEADERS,
                      json=patient_resource, timeout=30)
    print_call("POST", "/Patient",
               f"Create NHS Patient  (NHS# {nhs_number})", r)
    patient_id = extract_id(r)
    patient_ref = f"Patient/{patient_id}"

    # ── CALL 4: Create Severe Mental Health Diagnosis (ICD-10) ───────────────
    condition_resource = generate_condition(patient_ref, prac_ref)
    r = requests.post(f"{FHIR_BASE}/Condition", headers=HEADERS,
                      json=condition_resource, timeout=30)
    print_call("POST", "/Condition",
               "Record Severe Mental Health Diagnosis (ICD-10)", r)

    # ── CALL 5: Create GAF Score Observation ─────────────────────────────────
    obs_resource = generate_gaf_observation(patient_ref, prac_ref)
    r = requests.post(f"{FHIR_BASE}/Observation", headers=HEADERS,
                      json=obs_resource, timeout=30)
    print_call("POST", "/Observation",
               "Record GAF (Global Assessment of Functioning) Score", r)
    obs_id = extract_id(r)

    # ── CALL 6: Prescribe Antipsychotic Medication ───────────────────────────
    med_resource = generate_medication_request(patient_ref, prac_ref)
    r = requests.post(f"{FHIR_BASE}/MedicationRequest", headers=HEADERS,
                      json=med_resource, timeout=30)
    print_call("POST", "/MedicationRequest",
               "Prescribe Antipsychotic / Mood Stabiliser", r)

    # ── CALL 7: Create CMHT Outpatient Encounter ─────────────────────────────
    enc_resource = generate_encounter(patient_ref, prac_ref, org_ref)
    r = requests.post(f"{FHIR_BASE}/Encounter", headers=HEADERS,
                      json=enc_resource, timeout=30)
    print_call("POST", "/Encounter",
               "Record Community Mental Health Team (CMHT) Appointment", r)

    # ── CALL 8: Read Patient by FHIR ID ─────────────────────────────────────
    r = requests.get(f"{FHIR_BASE}/Patient/{patient_id}",
                     headers=HEADERS, timeout=30)
    print_call("GET", f"/Patient/{patient_id}",
               "Read Patient Record by FHIR ID", r)

    # ── CALL 9: Search Patient by NHS Number ─────────────────────────────────
    r = requests.get(
        f"{FHIR_BASE}/Patient",
        params={"identifier": f"https://fhir.nhs.uk/Id/nhs-number|{nhs_number}"},
        headers=HEADERS,
        timeout=30,
    )
    print_call("GET", f"/Patient?identifier=NHS|{nhs_number}",
               "Search Patient by NHS Number", r)

    # ── CALL 10: Search Active Conditions for Patient ────────────────────────
    r = requests.get(
        f"{FHIR_BASE}/Condition",
        params={"patient": patient_id, "clinical-status": "active"},
        headers=HEADERS,
        timeout=30,
    )
    print_call("GET", f"/Condition?patient={patient_id}&clinical-status=active",
               "Get Active Mental Health Conditions for Patient", r)

    # ── CALL 11: Search GAF Observations for Patient ────────────────────────
    r = requests.get(
        f"{FHIR_BASE}/Observation",
        params={"patient": patient_id, "category": "survey"},
        headers=HEADERS,
        timeout=30,
    )
    print_call("GET", f"/Observation?patient={patient_id}&category=survey",
               "Get Mental Health Assessment (GAF) Observations", r)

    # ── CALL 12: Update Patient — add mobile phone number ────────────────────
    updated_patient = {**patient_resource, "id": patient_id}
    updated_patient["telecom"] = [
        {"system": "phone", "value": "07700 900000", "use": "mobile"}
    ]
    r = requests.put(
        f"{FHIR_BASE}/Patient/{patient_id}",
        headers=HEADERS,
        json=updated_patient,
        timeout=30,
    )
    print_call("PUT", f"/Patient/{patient_id}",
               "Update Patient — Add Mobile Contact Number", r)

    # ── CALL 13: Search Active Medication Requests ───────────────────────────
    r = requests.get(
        f"{FHIR_BASE}/MedicationRequest",
        params={"patient": patient_id, "status": "active"},
        headers=HEADERS,
        timeout=30,
    )
    print_call("GET", f"/MedicationRequest?patient={patient_id}&status=active",
               "Get Active Medication Prescriptions for Patient", r)

    # ── CALL 14: Patient $everything (complete clinical record) ──────────────
    r = requests.get(
        f"{FHIR_BASE}/Patient/{patient_id}/$everything",
        headers=HEADERS,
        timeout=60,
    )
    print_call("GET", f"/Patient/{patient_id}/$everything",
               "Patient $everything — Full Clinical Summary", r)

    # ── CALL 15: POST Transaction Bundle (second patient + condition + GAF) ──
    p2 = generate_patient()
    c2 = generate_condition(f"urn:uuid:{p2['id']}", prac_ref)
    o2 = generate_gaf_observation(f"urn:uuid:{p2['id']}", prac_ref)

    bundle = {
        "resourceType": "Bundle",
        "type": "transaction",
        "entry": [
            {
                "fullUrl": f"urn:uuid:{p2['id']}",
                "resource": p2,
                "request": {"method": "POST", "url": "Patient"},
            },
            {
                "fullUrl": f"urn:uuid:{c2['id']}",
                "resource": c2,
                "request": {"method": "POST", "url": "Condition"},
            },
            {
                "fullUrl": f"urn:uuid:{o2['id']}",
                "resource": o2,
                "request": {"method": "POST", "url": "Observation"},
            },
        ],
    }
    r = requests.post(f"{FHIR_BASE}", headers=HEADERS, json=bundle, timeout=30)
    print_call("POST", "/",
               "Transaction Bundle — Admit Second Patient (Patient + Condition + GAF)", r)

    # ── Summary ──────────────────────────────────────────────────────────────
    print(f"\n{'═'*70}")
    print(f"  Demo complete — {_call_count} FHIR REST API calls executed")
    print(f"  Patient NHS#: {nhs_number}  |  FHIR ID: {patient_id}")
    print(f"  HAPI FHIR UI:  http://localhost:8080")
    print(f"  FHIR endpoint: {FHIR_BASE}")
    print(f"{'═'*70}\n")


if __name__ == "__main__":
    run()
