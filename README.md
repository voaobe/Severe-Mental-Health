# Severe Mental Health — NHS FHIR R4 Test Server

A full-stack FHIR R4 test environment for NHS severe mental health data,
demonstrating 15 REST API calls against a HAPI-compatible FHIR server.

## Stack

| Component | Technology |
|---|---|
| FHIR Server | `fhir_server.py` — Flask/Python FHIR R4 (in-memory) |
| Production server | `docker-compose.yml` — HAPI FHIR `hapiproject/hapi:latest` |
| NHS Data Generator | `generate_nhs_data.py` — FHIR R4 resources with NHS identifiers |
| API Demo | `fhir_api_demo.py` — 15 REST API calls |

## Quick Start

```bash
# Option A: Python server (no Docker needed)
python3 -m venv venv && source venv/bin/activate
pip install flask requests
python fhir_server.py &          # starts on :8080
python fhir_api_demo.py          # runs 15 API calls

# Option B: HAPI FHIR via Docker Compose
bash run_demo.sh                  # starts Docker, waits, runs demo
```

## FHIR Resources Generated

| Resource | NHS coding |
|---|---|
| `Patient` | NHS Number (`https://fhir.nhs.uk/Id/nhs-number`) |
| `Practitioner` | GMC Number (`https://fhir.hl7.org.uk/Id/gmc-number`) |
| `Organization` | ODS Code (`https://fhir.nhs.uk/Id/ods-organization-code`) |
| `Condition` | ICD-10 severe mental health (F20-F84) |
| `Observation` | LOINC 44240-2 GAF score |
| `MedicationRequest` | SNOMED antipsychotics and mood stabilisers |
| `Encounter` | SNOMED CMHT appointment types |

## 15 REST API Calls

| # | Method | Endpoint | Description |
|---|---|---|---|
| 1 | POST | /Organization | Create NHS Trust |
| 2 | POST | /Practitioner | Create Consultant Psychiatrist |
| 3 | POST | /Patient | Create NHS Patient with NHS Number |
| 4 | POST | /Condition | Record ICD-10 diagnosis |
| 5 | POST | /Observation | Record GAF score |
| 6 | POST | /MedicationRequest | Prescribe antipsychotic |
| 7 | POST | /Encounter | Record CMHT appointment |
| 8 | GET | /Patient/{id} | Read patient by FHIR ID |
| 9 | GET | /Patient?identifier=NHS\|{nhs-number} | Search by NHS number |
| 10 | GET | /Condition?patient={id}&clinical-status=active | Active diagnoses |
| 11 | GET | /Observation?patient={id}&category=survey | GAF assessments |
| 12 | PUT | /Patient/{id} | Update patient contact details |
| 13 | GET | /MedicationRequest?patient={id}&status=active | Active prescriptions |
| 14 | GET | /Patient/{id}/$everything | Full clinical summary |
| 15 | POST | / | Transaction bundle (Patient + Condition + GAF) |

## NHS Severe Mental Health Conditions (ICD-10)

- F20.0 Paranoid schizophrenia
- F20.1 Hebephrenic schizophrenia
- F25.0 Schizoaffective disorder
- F31.1/F31.2 Bipolar affective disorder
- F32.2/F32.3 Severe depressive episode
- F60.3 Emotionally unstable personality disorder
- F84.0 Autism spectrum disorder

## Files

```
docker-compose.yml      HAPI FHIR server (Docker)
fhir_server.py          Lightweight FHIR R4 server (Flask)
generate_nhs_data.py    NHS FHIR R4 resource generators
fhir_api_demo.py        15 REST API calls demo
requirements.txt        Python dependencies
run_demo.sh             One-command Docker demo launcher
```
