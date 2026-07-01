"""
Run with:
    pip install fastapi uvicorn pymongo python-dotenv@pip install "fastapi[standard]"
    uvicorn main:app --reload --host 0.0.0.0 --port 8000
    
"""

import os
from datetime import datetime, timezone
from typing import Optional, List

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient
from pymongo.collection import Collection
from dotenv import load_dotenv

# ── Config ────────────────────────────────────────────────────────────────────
load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME   = "pgx_registry"

# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="HMC PGx Registry API",
    description=(
        "RESTful API for the Helix Medical Centre Pharmacogenomics Registry. "
        "Exposes patient records, gene panel catalogues, genomic variants, "
        "and drug response observations through 10 analytical endpoints."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

# ── Database connection ───────────────────────────────────────────────────────
_client: Optional[MongoClient] = None


def get_db():
    global _client
    if _client is None:
        _client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=8000)
    return _client[DB_NAME]


# ── Helpers ───────────────────────────────────────────────────────────────────

from typing import Optional
def paginate(collection: Collection, pipeline: list, page: int, limit: int) -> dict:
    """
    Run an aggregation pipeline; apply skip/limit for pagination.
    Returns the standard response envelope: { total, page, limit, data }.
    """
    count_pipeline = pipeline + [{"$count": "total"}]
    count_result   = list(collection.aggregate(count_pipeline))
    total          = count_result[0]["total"] if count_result else 0

    data_pipeline = pipeline + [
        {"$skip":  (page - 1) * limit},
        {"$limit": limit},
        {"$project": {"_id": 0}},
    ]
    data = list(collection.aggregate(data_pipeline))

    return {"total": total, "page": page, "limit": limit, "data": data}


def find_paginated(collection: Collection, match: dict, page: int, limit: int,
                   sort: Optional[dict] = None) -> dict:
    """Paginate a simple find() query (no aggregation needed)."""
    total = collection.count_documents(match)
    cursor = collection.find(match, {"_id": 0})
    if sort:
        cursor = cursor.sort(list(sort.items()))
    data = list(cursor.skip((page - 1) * limit).limit(limit))
    return {"total": total, "page": page, "limit": limit, "data": data}


# ── Health ────────────────────────────────────────────────────────────────────

@app.get("/", tags=["Health"])
def root():
    return {"status": "ok", "message": "HMC PGx Registry API is running."}


@app.get("/api/health", tags=["Health"])
def health():
    try:
        get_db().command("ping")
        return {"status": "ok", "database": DB_NAME}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# ── AR1 ───────────────────────────────────────────────────────────────────────

@app.get(
    "/api/panels",
    tags=["AR1 – Gene Panels"],
    summary="AR1 — Filter gene panels by type, status, and/or manufacturer",
)
def ar1_filter_panels(
    panel_type:   Optional[str] = Query(None, description="e.g. Oncology | Pharmacogenomics | Cardiology | Rare Disease | Infectious Disease"),
    status:       Optional[str] = Query(None, description="e.g. Active | Deprecated | Under Review"),
    manufacturer: Optional[str] = Query(None, description="Partial match, case-insensitive"),
    page:  int = Query(1,  ge=1),
    limit: int = Query(20, ge=1, le=100),
):
    """
    AR1 — Retrieve gene panels filtered by one or more attributes.

    MongoDB pipeline:
    1. $match on panel_type, status, manufacturer (all optional)
    """
    db   = get_db()
    match: dict = {}

    if panel_type:
        match["panel_type"] = panel_type
    if status:
        match["status"] = status
    if manufacturer:
        match["manufacturer"] = {"$regex": manufacturer, "$options": "i"}

    return find_paginated(db.gene_panels, match, page, limit, sort={"panel_name": 1})


# ── AR2 ───────────────────────────────────────────────────────────────────────

@app.get(
    "/api/panels/{panel_id}/patients",
    tags=["AR2 – Panel Patients"],
    summary="AR2 — Retrieve patients who ordered a specific gene panel",
)
def ar2_patients_by_panel(
    panel_id: str,
    gender:   Optional[str] = Query(None, description="e.g. Male | Female | Non-binary"),
    ethnicity: Optional[str] = Query(None, description="e.g. Malay | Chinese | Indian"),
    site_id:  Optional[str] = Query(None, description="e.g. SITE-01"),
    page:  int = Query(1,  ge=1),
    limit: int = Query(20, ge=1, le=100),
):
    """
    AR2 — Given a panel, retrieve demographics of patients who ordered it,
    with optional narrowing by patient attributes.

    MongoDB pipeline:
    1. $match ordered_panels contains panel_id (and optional demographic filters)
    """
    db = get_db()

    # Verify panel exists
    if not db.gene_panels.find_one({"panel_id": panel_id}):
        raise HTTPException(status_code=404, detail=f"Panel '{panel_id}' not found.")

    match: dict = {"ordered_panels": panel_id}
    if gender:
        match["gender"] = gender
    if ethnicity:
        match["ethnicity"] = ethnicity
    if site_id:
        match["site_id"] = site_id

    return find_paginated(db.patients, match, page, limit)


# ── AR3 ───────────────────────────────────────────────────────────────────────

@app.get(
    "/api/patients",
    tags=["AR3 – Patient Search"],
    summary="AR3 — Search patients by demographic or clinical criteria",
)
def ar3_search_patients(
    gender:    Optional[str] = Query(None),
    ethnicity: Optional[str] = Query(None),
    site_id:   Optional[str] = Query(None),
    blood_type: Optional[str] = Query(None),
    icd10_code: Optional[str] = Query(None, description="Primary condition ICD-10 code, partial match"),
    page:  int = Query(1,  ge=1),
    limit: int = Query(20, ge=1, le=100),
):
    """
    AR3 — Search across the patient population using any combination of
    demographic and clinical attributes.

    MongoDB pipeline:
    1. $match on gender, ethnicity, site_id, blood_type, primary_condition.icd10_code
       (all optional; combined with implicit AND)
    """
    db = get_db()
    match: dict = {}

    if gender:
        match["gender"] = gender
    if ethnicity:
        match["ethnicity"] = ethnicity
    if site_id:
        match["site_id"] = site_id
    if blood_type:
        match["blood_type"] = blood_type
    if icd10_code:
        match["primary_condition.icd10_code"] = {"$regex": icd10_code, "$options": "i"}

    return find_paginated(db.patients, match, page, limit)


# ── AR4 ───────────────────────────────────────────────────────────────────────

@app.get(
    "/api/patients/{patient_id}/drug-responses",
    tags=["AR4 – Patient Drug Responses"],
    summary="AR4 — Retrieve all drug responses for a patient",
)
def ar4_drug_responses_by_patient(
    patient_id:    str,
    response_type: Optional[str] = Query(None, description="Efficacy | Toxicity | Dosing"),
    drug_class:    Optional[str] = Query(None),
    outcome:       Optional[str] = Query(None),
    page:  int = Query(1,  ge=1),
    limit: int = Query(20, ge=1, le=100),
):
    """
    AR4 — Given a patient, retrieve all drug response records across all
    panels and variants, with optional filters.

    MongoDB pipeline:
    1. $match patient_id (and optional response_type, drug_class, outcome)
    """
    db = get_db()

    if not db.patients.find_one({"patient_id": patient_id}):
        raise HTTPException(status_code=404, detail=f"Patient '{patient_id}' not found.")

    match: dict = {"patient_id": patient_id}
    if response_type:
        match["response_type"] = response_type
    if drug_class:
        match["drug_class"] = drug_class
    if outcome:
        match["outcome"] = outcome

    return find_paginated(db.drug_responses, match, page, limit)


# ── AR5 ───────────────────────────────────────────────────────────────────────

@app.get(
    "/api/drug-responses/summary-by-drug-class",
    tags=["AR5 – Drug Class Summary"],
    summary="AR5 — Drug response counts grouped by drug class with toxicity proportion",
)
def ar5_drug_class_summary(
    panel_id: Optional[str] = Query(None, description="Scope to a specific panel"),
):
    """
    AR5 — Aggregate drug response records grouped by drug class.
    Returns total count and proportion classified as Toxicity for each class.

    MongoDB aggregation pipeline:
    1. $match (optional panel filter)
    2. $group by drug_class: total count + count where response_type == 'Toxicity'
    3. $addFields to compute toxicity_proportion
    4. $sort by total_responses descending
    """
    db = get_db()
    match_stage: dict = {}
    if panel_id:
        match_stage["panel_id"] = panel_id

    pipeline = []
    if match_stage:
        pipeline.append({"$match": match_stage})

    pipeline += [
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

    data = list(get_db().drug_responses.aggregate(pipeline))
    return {"total": len(data), "page": 1, "limit": len(data), "data": data}


# ── AR6 ───────────────────────────────────────────────────────────────────────

@app.get(
    "/api/panels/{panel_id}/variants",
    tags=["AR6 – Panel Variant Catalogue"],
    summary="AR6 — Retrieve variant catalogue for a gene panel",
)
def ar6_variants_by_panel(
    panel_id:             str,
    clinical_significance: Optional[str] = Query(None, description="e.g. Pathogenic | Likely pathogenic | VUS"),
    evidence_level:       Optional[str] = Query(None, description="1A | 1B | 2A | 2B | 3 | 4"),
    gene_symbol:          Optional[str] = Query(None),
    page:  int = Query(1,  ge=1),
    limit: int = Query(50, ge=1, le=200),
):
    """
    AR6 — Given a panel, retrieve its full variant catalogue with optional
    filters by clinical significance, evidence level, or gene symbol.

    MongoDB pipeline:
    1. $match panel_id (plus optional clinical_significance, evidence_level, gene_symbol)
    """
    db = get_db()

    if not db.gene_panels.find_one({"panel_id": panel_id}):
        raise HTTPException(status_code=404, detail=f"Panel '{panel_id}' not found.")

    match: dict = {"panel_id": panel_id}
    if clinical_significance:
        match["clinical_significance"] = {"$regex": clinical_significance, "$options": "i"}
    if evidence_level:
        match["evidence_level"] = evidence_level
    if gene_symbol:
        match["gene_symbol"] = gene_symbol.upper()

    return find_paginated(db.variants, match, page, limit)


# ── AR7 ───────────────────────────────────────────────────────────────────────

@app.get(
    "/api/variants/{variant_id}/response-matrix",
    tags=["AR7 – Variant Response Matrix"],
    summary="AR7 — Cross-tabulation of drug responses by outcome and response type for a variant",
)
def ar7_variant_response_matrix(variant_id: str):
    """
    AR7 — For a given variant, produce a cross-tabulation of all associated
    drug responses by outcome category and response type.

    MongoDB aggregation pipeline:
    1. $match variant_id
    2. $group by { outcome, response_type }, count occurrences
    3. $group by outcome to nest response_type counts in an array
    4. $project to reshape into a matrix-friendly structure
    """
    db = get_db()

    if not db.variants.find_one({"variant_id": variant_id}):
        raise HTTPException(status_code=404, detail=f"Variant '{variant_id}' not found.")

    pipeline = [
        {"$match": {"variant_id": variant_id}},
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

    data = list(db.drug_responses.aggregate(pipeline))
    return {"variant_id": variant_id, "total_rows": len(data), "matrix": data}


# ── AR8 ───────────────────────────────────────────────────────────────────────

@app.get(
    "/api/patients/comorbidity-burden",
    tags=["AR8 – Comorbidity & Drug Burden"],
    summary="AR8 — Patients with comorbidity count above threshold and their drug response burden",
)
def ar8_comorbidity_burden(
    min_comorbidities: int = Query(2, ge=0, description="Minimum number of comorbidities (inclusive)"),
    page:  int = Query(1,  ge=1),
    limit: int = Query(20, ge=1, le=100),
):
    """
    AR8 — Identify patients whose comorbidity count exceeds a given threshold
    and return their total and toxicity drug response counts.

    MongoDB aggregation pipeline:
    1. $addFields: comorbidity_count = $size of comorbidities array
    2. $match: comorbidity_count >= min_comorbidities
    3. $lookup drug_responses for each patient
    4. $addFields: total_responses + toxicity_count from looked-up array
    5. $project: clean output
    """
    db = get_db()

    pipeline = [
        {"$addFields": {"comorbidity_count": {"$size": "$comorbidities"}}},
        {"$match": {"comorbidity_count": {"$gte": min_comorbidities}}},
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
                "patient_id": 1,
                "name": 1,
                "site_id": 1,
                "comorbidity_count": 1,
                "comorbidities": 1,
                "total_responses": 1,
                "toxicity_count": 1,
            }
        },
        {"$sort": {"comorbidity_count": -1, "toxicity_count": -1}},
    ]

    return paginate(db.patients, pipeline, page, limit)


# ── AR9 ───────────────────────────────────────────────────────────────────────

@app.get(
    "/api/variants/by-gene",
    tags=["AR9 – Variants & Responses by Gene"],
    summary="AR9 — Retrieve variants and their drug response counts for a gene symbol",
)
def ar9_variants_by_gene(
    gene_symbol: str = Query(..., description="HGNC gene symbol, e.g. CYP2D6"),
):
    """
    AR9 — Retrieve all variants for a gene and for each return the count of
    associated drug response records.

    This implements the two-step indirect path described in Section 3:
    drug_response → gene is resolved via the variants collection.

    MongoDB aggregation pipeline:
    1. $match gene_symbol in variants collection
    2. $lookup drug_responses on variant_id
    3. $addFields response_count = $size of looked-up array
    4. $project: clean output, drop large arrays
    """
    db = get_db()

    pipeline = [
        {"$match": {"gene_symbol": gene_symbol.upper()}},
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
                "variant_id": 1,
                "panel_id": 1,
                "gene_symbol": 1,
                "hgvs_notation": 1,
                "clinical_significance": 1,
                "evidence_level": 1,
                "associated_condition": 1,
                "response_count": 1,
            }
        },
        {"$sort": {"response_count": -1}},
    ]

    data = list(db.variants.aggregate(pipeline))

    if not data:
        raise HTTPException(
            status_code=404,
            detail=f"No variants found for gene symbol '{gene_symbol.upper()}'."
        )

    total_responses = sum(v["response_count"] for v in data)
    return {
        "gene_symbol": gene_symbol.upper(),
        "variant_count": len(data),
        "total_response_count": total_responses,
        "data": data,
    }


# ── AR10 ──────────────────────────────────────────────────────────────────────

@app.get(
    "/api/drug-responses/monthly-trend",
    tags=["AR10 – Monthly Trend"],
    summary="AR10 — Time-series of drug response records grouped by year and month",
)
def ar10_monthly_trend(
    panel_id:      Optional[str] = Query(None, description="Scope to a specific panel"),
    response_type: Optional[str] = Query(None, description="Efficacy | Toxicity | Dosing"),
    year_from:     Optional[int] = Query(None, description="Start year (inclusive), e.g. 2020"),
    year_to:       Optional[int] = Query(None, description="End year (inclusive), e.g. 2024"),
):
    """
    AR10 — Produce a monthly time-series of drug responses, optionally scoped
    to a panel or response type, with optional year range.

    MongoDB aggregation pipeline:
    1. $match (optional panel_id, response_type, year range via $expr)
    2. $group by { year: $year(reported_on), month: $month(reported_on) }
    3. $sort by year, month ascending
    4. $project: human-readable year_month label
    """
    db = get_db()

    match: dict = {}
    if panel_id:
        match["panel_id"] = panel_id
    if response_type:
        match["response_type"] = response_type
    if year_from or year_to:
        date_filter: dict = {}
        if year_from:
            date_filter["$gte"] = datetime(year_from, 1, 1, tzinfo=timezone.utc)
        if year_to:
            date_filter["$lte"] = datetime(year_to, 12, 31, tzinfo=timezone.utc)
        match["reported_on"] = date_filter

    pipeline = []
    if match:
        pipeline.append({"$match": match})

    pipeline += [
        {
            "$group": {
                "_id": {
                    "year":  {"$year":  "$reported_on"},
                    "month": {"$month": "$reported_on"},
                },
                "count": {"$sum": 1},
                "toxicity_count": {
                    "$sum": {"$cond": [{"$eq": ["$response_type", "Toxicity"]}, 1, 0]}
                },
                "efficacy_count": {
                    "$sum": {"$cond": [{"$eq": ["$response_type", "Efficacy"]}, 1, 0]}
                },
                "dosing_count": {
                    "$sum": {"$cond": [{"$eq": ["$response_type", "Dosing"]}, 1, 0]}
                },
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
                        {"$toString": "$_id.year"},
                        "-",
                        {"$cond": [
                            {"$lt": ["$_id.month", 10]},
                            {"$concat": ["0", {"$toString": "$_id.month"}]},
                            {"$toString": "$_id.month"},
                        ]},
                    ]
                },
                "count": 1,
                "toxicity_count": 1,
                "efficacy_count": 1,
                "dosing_count": 1,
            }
        },
    ]

    data = list(db.drug_responses.aggregate(pipeline))
    return {"total_months": len(data), "data": data}
