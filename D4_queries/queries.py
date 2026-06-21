import os
import json
from datetime import datetime, timezone
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME   = "HMC"

client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=8000)
db     = client[DB_NAME]

def print_header(ar: str, title: str):
    print("\n" + "═" * 70)
    print(f"  {ar} — {title}")
    print("═" * 70)


def print_results(results: list, max_docs: int = 5):
    shown = results[:max_docs]
    for doc in shown:
        print(json.dumps(doc, indent=2, default=str))
    if len(results) > max_docs:
        print(f"  ... ({len(results) - max_docs} more documents)")
    print(f"\n  → Total results: {len(results)}")

#AR1 — Filter gene panels by type and/or status
print_header("AR1", "Filter gene panels by type and/or status")
print("Example: panel_type='Oncology', status='Active'")

PANEL_TYPE = "Oncology"
STATUS     = "Active"

ar1_match = {}
if PANEL_TYPE: ar1_match["panel_type"] = PANEL_TYPE
if STATUS:     ar1_match["status"]     = STATUS

ar1_pipeline = [
    {"$match": ar1_match},
    {"$project": {
        "_id": 0,
        "panel_id": 1, "panel_name": 1, "panel_type": 1,
        "version": 1, "status": 1, "manufacturer": 1,
        "turnaround_days": 1, "regulatory_clearance": 1,
    }},
    {"$sort": {"panel_name": 1}},
]
ar1_results = list(db.gene_panels.aggregate(ar1_pipeline))
print_results(ar1_results)

# AR2 — Retrieve all patients for a specific gene panel
print_header("AR2", "Retrieve all patients for a specific gene panel")
print("Example: panel_id='PNL-000201' (CYP Metaboliser Panel), gender='Female'")

PANEL_ID = "PNL-000201"
GENDER   = "Female"

ar2_match = {"ordered_panels": PANEL_ID}
if GENDER: ar2_match["gender"] = GENDER

ar2_pipeline = [
    {"$match": ar2_match},
    {"$project": {
        "_id": 0,
        "patient_id": 1, "name": 1, "gender": 1, "ethnicity": 1,
        "date_of_birth": 1, "site_id": 1, "primary_condition": 1,
    }},
    {"$sort": {"name": 1}},
]
ar2_results = list(db.patients.aggregate(ar2_pipeline))
print_results(ar2_results)

# AR3 — Search patients by demographic or clinical criteria
print_header("AR3", "Search patients by demographic or clinical criteria")
print("Example: ethnicity='Chinese', site_id='SITE-01'")

ETHNICITY = "Chinese"
SITE_ID   = "SITE-01"

ar3_match = {}
if ETHNICITY: ar3_match["ethnicity"] = ETHNICITY
if SITE_ID:   ar3_match["site_id"]   = SITE_ID

ar3_pipeline = [
    {"$match": ar3_match},
    {"$project": {
        "_id": 0,
        "patient_id": 1, "name": 1, "gender": 1, "ethnicity": 1,
        "site_id": 1, "blood_type": 1, "primary_condition.icd10_code": 1,
        "primary_condition.description": 1,
    }},
    {"$sort": {"name": 1}},
]
ar3_results = list(db.patients.aggregate(ar3_pipeline))
print_results(ar3_results)

# AR4 — Retrieve all drug responses for a patient
print_header("AR4", "Retrieve all drug responses for a patient")
print("Example: patient_id='PT-001001', response_type='Toxicity'")

PATIENT_ID    = "PT-001001"
RESPONSE_TYPE = "Toxicity"

ar4_match = {"patient_id": PATIENT_ID}
if RESPONSE_TYPE: ar4_match["response_type"] = RESPONSE_TYPE

ar4_pipeline = [
    {"$match": ar4_match},
    {"$project": {
        "_id": 0,
        "response_id": 1, "panel_id": 1, "variant_id": 1,
        "drug_name": 1, "drug_class": 1, "response_type": 1,
        "outcome": 1, "phenotype_observed": 1, "ctcae_grade": 1,
        "recommendation": 1, "reported_on": 1,
    }},
    {"$sort": {"reported_on": -1}},
]
ar4_results = list(db.drug_responses.aggregate(ar4_pipeline))
print_results(ar4_results)

# AR5 — Drug response summary grouped by drug class
print_header("AR5", "Drug response summary grouped by drug class")
print("Returns counts and toxicity proportion per drug class.")

ar5_pipeline = [
    {
        "$group": {
            "_id": "$drug_class",
            "total_responses": {"$sum": 1},
            "toxicity_count": {
                "$sum": {"$cond": [{"$eq": ["$response_type", "Toxicity"]}, 1, 0]}
            },
        }
    },
    {
        "$addFields": {
            "drug_class": "$_id",
            "toxicity_proportion": {
                "$round": [
                    {"$divide": ["$toxicity_count", "$total_responses"]},
                    4,
                ]
            },
        }
    },
    {"$project": {"_id": 0}},
    {"$sort": {"total_responses": -1}},
]
ar5_results = list(db.drug_responses.aggregate(ar5_pipeline))
print_results(ar5_results, max_docs=10)

# AR6 — Variant catalogue for a gene panel
print_header("AR6", "Variant catalogue for a gene panel")
print("Example: panel_id='PNL-000101', clinical_significance='Pathogenic'")

PANEL_ID_AR6  = "PNL-000101"
SIGNIFICANCE  = "Pathogenic"

ar6_match = {"panel_id": PANEL_ID_AR6}
if SIGNIFICANCE: ar6_match["clinical_significance"] = SIGNIFICANCE

ar6_pipeline = [
    {"$match": ar6_match},
    {"$project": {
        "_id": 0,
        "variant_id": 1, "gene_symbol": 1, "hgvs_notation": 1,
        "variant_type": 1, "clinical_significance": 1,
        "evidence_level": 1, "associated_condition": 1, "rsid": 1,
    }},
    {"$sort": {"evidence_level": 1, "gene_symbol": 1}},
]
ar6_results = list(db.variants.aggregate(ar6_pipeline))
print_results(ar6_results)

# AR7 — Drug response outcome matrix for a variant
print_header("AR7", "Drug response outcome matrix for a variant")
print("Example: variant_id='VAR-000007' (CYP2D6 deletion)")

VARIANT_ID_AR7 = "VAR-000007"

ar7_pipeline = [
    {"$match": {"variant_id": VARIANT_ID_AR7}},
    {
        "$group": {
            "_id": {"outcome": "$outcome", "response_type": "$response_type"},
            "count": {"$sum": 1},
        }
    },
    {
        "$group": {
            "_id": "$_id.outcome",
            "breakdown": {
                "$push": {
                    "response_type": "$_id.response_type",
                    "count": "$count",
                }
            },
            "total": {"$sum": "$count"},
        }
    },
    {
        "$project": {
            "_id": 0,
            "outcome": "$_id",
            "breakdown": 1,
            "total": 1,
        }
    },
    {"$sort": {"total": -1}},
]
ar7_results = list(db.drug_responses.aggregate(ar7_pipeline))
print_results(ar7_results)

# AR8 — Patient comorbidity and drug response burden
print_header("AR8", "Patient comorbidity and drug response burden")
print("Example: min_comorbidities=2")

MIN_COMORBIDITIES = 2

ar8_pipeline = [
    {"$addFields": {"comorbidity_count": {"$size": "$comorbidities"}}},
    {"$match": {"comorbidity_count": {"$gte": MIN_COMORBIDITIES}}},
    {
        "$lookup": {
            "from":         "drug_responses",
            "localField":   "patient_id",
            "foreignField": "patient_id",
            "as":           "responses",
        }
    },
    {
        "$addFields": {
            "total_responses": {"$size": "$responses"},
            "toxicity_count": {
                "$size": {
                    "$filter": {
                        "input": "$responses",
                        "cond":  {"$eq": ["$$this.response_type", "Toxicity"]},
                    }
                }
            },
        }
    },
    {
        "$project": {
            "_id": 0,
            "patient_id": 1, "name": 1, "site_id": 1,
            "comorbidity_count": 1, "total_responses": 1, "toxicity_count": 1,
        }
    },
    {"$sort": {"comorbidity_count": -1, "toxicity_count": -1}},
]
ar8_results = list(db.patients.aggregate(ar8_pipeline))
print_results(ar8_results)

# AR9 — Variants and responses by gene symbol
print_header("AR9", "Variants and responses by gene symbol")
print("Example: gene_symbol='CYP2D6'")
print("Two-step resolution: drug_response → gene is resolved via variants collection.")

GENE_SYMBOL = "CYP2D6"

ar9_pipeline = [
    {"$match": {"gene_symbol": GENE_SYMBOL}},
    {
        "$lookup": {
            "from":         "drug_responses",
            "localField":   "variant_id",
            "foreignField": "variant_id",
            "as":           "responses",
        }
    },
    {
        "$addFields": {
            "response_count": {"$size": "$responses"}
        }
    },
    {
        "$project": {
            "_id": 0,
            "variant_id": 1, "panel_id": 1, "gene_symbol": 1,
            "hgvs_notation": 1, "clinical_significance": 1,
            "evidence_level": 1, "response_count": 1,
        }
    },
    {"$sort": {"response_count": -1}},
]
ar9_results = list(db.variants.aggregate(ar9_pipeline))
print_results(ar9_results)

# AR10 — Monthly drug response trend over time
print_header("AR10", "Monthly drug response trend over time")
print("Example: scoped to response_type='Toxicity', years 2020–2024")

RESPONSE_TYPE_AR10 = "Toxicity"
YEAR_FROM          = 2020
YEAR_TO            = 2024

ar10_match: dict = {}
if RESPONSE_TYPE_AR10:
    ar10_match["response_type"] = RESPONSE_TYPE_AR10
if YEAR_FROM or YEAR_TO:
    date_filter: dict = {}
    if YEAR_FROM:
        date_filter["$gte"] = datetime(YEAR_FROM, 1, 1, tzinfo=timezone.utc)
    if YEAR_TO:
        date_filter["$lte"] = datetime(YEAR_TO, 12, 31, tzinfo=timezone.utc)
    ar10_match["reported_on"] = date_filter

ar10_pipeline = []
if ar10_match:
    ar10_pipeline.append({"$match": ar10_match})

ar10_pipeline += [
    {
        "$group": {
            "_id": {
                "year":  {"$year":  "$reported_on"},
                "month": {"$month": "$reported_on"},
            },
            "count": {"$sum": 1},
        }
    },
    {"$sort": {"_id.year": 1, "_id.month": 1}},
    {
        "$project": {
            "_id": 0,
            "year":  "$_id.year",
            "month": "$_id.month",
            "year_month": {
                "$concat": [
                    {"$toString": "$_id.year"}, "-",
                    {"$cond": [
                        {"$lt": ["$_id.month", 10]},
                        {"$concat": ["0", {"$toString": "$_id.month"}]},
                        {"$toString": "$_id.month"},
                    ]},
                ]
            },
            "count": 1,
        }
    },
]
ar10_results = list(db.drug_responses.aggregate(ar10_pipeline))
print_results(ar10_results, max_docs=12)

print("\n" + "═" * 70)
print("  D4 Queries complete — all 10 ARs demonstrated.")
print("═" * 70)

client.close()
