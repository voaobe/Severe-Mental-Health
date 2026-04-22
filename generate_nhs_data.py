"""
NHS FHIR R4 data generator for severe mental health scenarios.
Generates realistic NHS-coded resources: patients, practitioners,
organizations, conditions, observations, medication requests, and encounters.
"""
import random
import uuid
from datetime import datetime, timedelta


def generate_nhs_number():
    """Generate a valid-format NHS number (10 digits)."""
    return f"{random.randint(100, 999)}{random.randint(100, 999)}{random.randint(1000, 9999)}"


def generate_organization():
    trusts = [
        ("Mersey Care NHS Foundation Trust", "RW4"),
        ("South London and Maudsley NHS Foundation Trust", "RV5"),
        ("Oxleas NHS Foundation Trust", "RJ6"),
        ("Greater Manchester Mental Health NHS Foundation Trust", "NTW"),
        ("Camden and Islington NHS Foundation Trust", "RP6"),
    ]
    name, ods_code = random.choice(trusts)
    return {
        "resourceType": "Organization",
        "id": str(uuid.uuid4()),
        "identifier": [
            {
                "system": "https://fhir.nhs.uk/Id/ods-organization-code",
                "value": ods_code,
            }
        ],
        "active": True,
        "type": [
            {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/organization-type",
                        "code": "prov",
                        "display": "Healthcare Provider",
                    }
                ]
            }
        ],
        "name": name,
        "telecom": [
            {
                "system": "phone",
                "value": f"0{random.randint(1000,9999)} {random.randint(100000,999999)}",
                "use": "work",
            }
        ],
        "address": [{"use": "work", "type": "both", "country": "England"}],
    }


def generate_practitioner():
    first_names = ["James", "Sarah", "Mohammed", "Emily", "David", "Priya", "Thomas", "Aisha"]
    last_names = ["Smith", "Johnson", "Ahmed", "Williams", "Brown", "Patel", "Jones", "Khan"]
    first = random.choice(first_names)
    last = random.choice(last_names)
    gmc_number = "".join([str(random.randint(0, 9)) for _ in range(7)])
    return {
        "resourceType": "Practitioner",
        "id": str(uuid.uuid4()),
        "identifier": [
            {
                "system": "https://fhir.hl7.org.uk/Id/gmc-number",
                "value": gmc_number,
            }
        ],
        "active": True,
        "name": [{"use": "official", "prefix": ["Dr"], "family": last, "given": [first]}],
        "qualification": [
            {
                "code": {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/v2-0360",
                            "code": "MD",
                            "display": "Doctor of Medicine",
                        }
                    ],
                    "text": "Consultant Psychiatrist",
                }
            }
        ],
    }


def generate_patient(nhs_number=None):
    if not nhs_number:
        nhs_number = generate_nhs_number()
    first_names_m = ["Oliver", "George", "Harry", "Jack", "Charlie", "Noah", "Jacob", "Alfie"]
    first_names_f = ["Olivia", "Amelia", "Isla", "Ava", "Mia", "Poppy", "Ella", "Lily"]
    last_names = ["Smith", "Jones", "Williams", "Taylor", "Brown", "Davies", "Evans", "Wilson"]
    gender = random.choice(["male", "female"])
    first = random.choice(first_names_m if gender == "male" else first_names_f)
    last = random.choice(last_names)
    dob = datetime.now() - timedelta(days=random.randint(18 * 365, 65 * 365))
    postcodes = ["SW1A 1AA", "M1 1AD", "B1 1BB", "LS1 1BA", "E1 6RF", "BS1 1AA", "L1 1JH"]
    ethnicity_options = [
        ("A", "British"),
        ("B", "Irish"),
        ("D", "Mixed - White and Black Caribbean"),
        ("H", "Asian or Asian British - Indian"),
        ("J", "Asian or Asian British - Pakistani"),
    ]
    ethnicity_code, ethnicity_display = random.choice(ethnicity_options)
    return {
        "resourceType": "Patient",
        "id": str(uuid.uuid4()),
        "identifier": [
            {
                "system": "https://fhir.nhs.uk/Id/nhs-number",
                "value": nhs_number,
            }
        ],
        "active": True,
        "name": [{"use": "official", "family": last, "given": [first]}],
        "gender": gender,
        "birthDate": dob.strftime("%Y-%m-%d"),
        "address": [
            {"use": "home", "postalCode": random.choice(postcodes), "country": "England"}
        ],
        "communication": [
            {
                "language": {
                    "coding": [
                        {
                            "system": "urn:ietf:bcp:47",
                            "code": "en",
                            "display": "English",
                        }
                    ]
                },
                "preferred": True,
            }
        ],
        "extension": [
            {
                "url": "https://fhir.hl7.org.uk/StructureDefinition/Extension-UKCore-EthnicCategory",
                "valueCodeableConcept": {
                    "coding": [
                        {
                            "system": "https://fhir.hl7.org.uk/CodeSystem/UKCore-EthnicCategory",
                            "code": ethnicity_code,
                            "display": ethnicity_display,
                        }
                    ]
                },
            }
        ],
    }


# ICD-10 severe mental health conditions
MENTAL_HEALTH_CONDITIONS = [
    ("F20.0", "Paranoid schizophrenia"),
    ("F20.1", "Hebephrenic schizophrenia"),
    ("F25.0", "Schizoaffective disorder, manic type"),
    ("F31.1", "Bipolar affective disorder, current episode manic without psychotic symptoms"),
    ("F31.2", "Bipolar affective disorder, current episode manic with psychotic symptoms"),
    ("F32.2", "Severe depressive episode without psychotic symptoms"),
    ("F32.3", "Severe depressive episode with psychotic symptoms"),
    ("F60.3", "Emotionally unstable personality disorder"),
    ("F84.0", "Childhood autism"),
    ("F41.1", "Generalised anxiety disorder"),
]


def generate_condition(patient_ref, practitioner_ref):
    code, display = random.choice(MENTAL_HEALTH_CONDITIONS)
    onset = datetime.now() - timedelta(days=random.randint(30, 3650))
    return {
        "resourceType": "Condition",
        "id": str(uuid.uuid4()),
        "clinicalStatus": {
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
                    "code": "active",
                    "display": "Active",
                }
            ]
        },
        "verificationStatus": {
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/condition-ver-status",
                    "code": "confirmed",
                    "display": "Confirmed",
                }
            ]
        },
        "category": [
            {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/condition-category",
                        "code": "encounter-diagnosis",
                        "display": "Encounter Diagnosis",
                    }
                ]
            }
        ],
        "code": {
            "coding": [
                {
                    "system": "http://hl7.org/fhir/sid/icd-10",
                    "code": code,
                    "display": display,
                }
            ],
            "text": display,
        },
        "subject": {"reference": patient_ref},
        "recorder": {"reference": practitioner_ref},
        "onsetDateTime": onset.strftime("%Y-%m-%d"),
        "recordedDate": datetime.now().strftime("%Y-%m-%d"),
    }


def generate_gaf_observation(patient_ref, practitioner_ref):
    """Create a GAF (Global Assessment of Functioning) score observation."""
    gaf_score = random.randint(10, 70)
    return {
        "resourceType": "Observation",
        "id": str(uuid.uuid4()),
        "status": "final",
        "category": [
            {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                        "code": "survey",
                        "display": "Survey",
                    }
                ]
            }
        ],
        "code": {
            "coding": [
                {
                    "system": "http://loinc.org",
                    "code": "44240-2",
                    "display": "Global Assessment of Functioning [GAF]",
                }
            ],
            "text": "GAF Score",
        },
        "subject": {"reference": patient_ref},
        "performer": [{"reference": practitioner_ref}],
        "effectiveDateTime": datetime.now().strftime("%Y-%m-%dT%H:%M:%S+00:00"),
        "valueQuantity": {
            "value": gaf_score,
            "unit": "score",
            "system": "http://unitsofmeasure.org",
            "code": "{score}",
        },
        "interpretation": [
            {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation",
                        "code": "L" if gaf_score < 40 else "N",
                        "display": "Low" if gaf_score < 40 else "Normal",
                    }
                ]
            }
        ],
        "note": [
            {
                "text": f"GAF score of {gaf_score} recorded during routine psychiatric assessment"
            }
        ],
    }


ANTIPSYCHOTICS = [
    ("372687004", "Olanzapine 10mg tablets", "10"),
    ("372726003", "Risperidone 2mg tablets", "2"),
    ("386849001", "Quetiapine 200mg tablets", "200"),
    ("387207008", "Aripiprazole 15mg tablets", "15"),
    ("387248006", "Clozapine 100mg tablets", "100"),
    ("372682005", "Lithium carbonate 400mg modified-release tablets", "400"),
]


def generate_medication_request(patient_ref, practitioner_ref):
    snomed_code, display, dose_value = random.choice(ANTIPSYCHOTICS)
    return {
        "resourceType": "MedicationRequest",
        "id": str(uuid.uuid4()),
        "status": "active",
        "intent": "order",
        "medicationCodeableConcept": {
            "coding": [
                {
                    "system": "http://snomed.info/sct",
                    "code": snomed_code,
                    "display": display,
                }
            ],
            "text": display,
        },
        "subject": {"reference": patient_ref},
        "requester": {"reference": practitioner_ref},
        "authoredOn": datetime.now().strftime("%Y-%m-%dT%H:%M:%S+00:00"),
        "dosageInstruction": [
            {
                "text": f"{display} - take once daily",
                "timing": {
                    "repeat": {"frequency": 1, "period": 1, "periodUnit": "d"}
                },
                "route": {
                    "coding": [
                        {
                            "system": "http://snomed.info/sct",
                            "code": "26643006",
                            "display": "Oral route",
                        }
                    ]
                },
                "doseAndRate": [
                    {
                        "type": {
                            "coding": [
                                {
                                    "system": "http://terminology.hl7.org/CodeSystem/dose-rate-type",
                                    "code": "ordered",
                                    "display": "Ordered",
                                }
                            ]
                        },
                        "doseQuantity": {
                            "value": float(dose_value),
                            "unit": "mg",
                            "system": "http://unitsofmeasure.org",
                            "code": "mg",
                        },
                    }
                ],
            }
        ],
        "dispenseRequest": {
            "quantity": {
                "value": 28,
                "unit": "tablets",
                "system": "http://snomed.info/sct",
                "code": "428673006",
            }
        },
    }


def generate_encounter(patient_ref, practitioner_ref, organization_ref):
    encounter_types = [
        ("11429006", "Consultation"),
        ("185389009", "Follow-up visit"),
        ("270427003", "Patient-initiated encounter"),
        ("386473003", "Telephone consultation"),
    ]
    code, display = random.choice(encounter_types)
    start = datetime.now() - timedelta(days=random.randint(1, 30))
    end = start + timedelta(hours=1)
    return {
        "resourceType": "Encounter",
        "id": str(uuid.uuid4()),
        "status": "finished",
        "class": {
            "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
            "code": "AMB",
            "display": "ambulatory",
        },
        "type": [
            {
                "coding": [
                    {
                        "system": "http://snomed.info/sct",
                        "code": code,
                        "display": display,
                    }
                ],
                "text": display,
            }
        ],
        "subject": {"reference": patient_ref},
        "participant": [
            {
                "type": [
                    {
                        "coding": [
                            {
                                "system": "http://terminology.hl7.org/CodeSystem/v3-ParticipationType",
                                "code": "PPRF",
                                "display": "primary performer",
                            }
                        ]
                    }
                ],
                "individual": {"reference": practitioner_ref},
            }
        ],
        "period": {
            "start": start.strftime("%Y-%m-%dT%H:%M:%S+00:00"),
            "end": end.strftime("%Y-%m-%dT%H:%M:%S+00:00"),
        },
        "serviceProvider": {"reference": organization_ref},
        "reasonCode": [
            {
                "coding": [
                    {
                        "system": "http://snomed.info/sct",
                        "code": "709814003",
                        "display": "Severe mental illness",
                    }
                ]
            }
        ],
    }
