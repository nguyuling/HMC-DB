
#! connect to mongodb
from pymongo import MongoClient
client = MongoClient("mongodb+srv://dbAdmin:123abc@cluster0.iuvvkqs.mongodb.net/")
db = client["HMC"]

#! define the functions to parse data
def parse_array(value, delimiter="|"):
    if not value or str(value).strip()=="" or str(value).lower()=="nan": return [] # if no items, return empty array
    return [item.strip() for item in str(value).split(delimiter) if item.strip()] # else return items 

def parse_int(value):
    if not value or str(value).strip()=="" or str(value).lower()=="nan": return None
    return int(float(value))

def parse_string(value):
    if not value or str(value).strip()=="" or str(value).lower()=="nan": return None
    return str(value).strip()

import csv
#! ingest collection 1: patients
def ingest_patients(csv_path="data/pgx-patients.csv"):
    collection = db["patients"]
    collection.delete_many({})
    documents = []
    
    with open(csv_path, mode='r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            doc = {
                "patient_id": parse_string(row.get("patient_id")),
                "name": parse_string(row.get("name")),
                "date_of_birth": parse_string(row.get("date_of_birth")),
                "gender": parse_string(row.get("gender")),
                "ethnicity": parse_string(row.get("ethnicity")),
                "blood_type": parse_string(row.get("blood_type")),
                "primary_condition": {
                    "icd10_code": parse_string(row.get("icd10_code")),
                    "description": parse_string(row.get("primary_description")),
                    "diagnosed_on": parse_string(row.get("diagnosed_on"))
                },
                "comorbidities": parse_array(row.get("comorbidities")),
                "site_id": parse_string(row.get("site_id")),
                "ordered_panels": parse_array(row.get("ordered_panels")),
                "contact_info": {
                    "email": parse_string(row.get("contact_email")),
                    "phone": parse_string(row.get("contact_phone")),
                    "emergency_contact": parse_string(row.get("emergency_contact")),
                },
                "created_at": parse_string(row.get("created_at"))
            }
            documents.append(doc)
            
    if documents:
        collection.insert_many(documents)
        print(f"successfully import {len(documents)} documents into patients collection.")
        
#! ingest collection 2: gene_panels
def ingest_gene_panels(csv_path="data/pgx_gene_panels.csv"):
    collection = db["gene_panels"]
    collection.delete_many({})
    documents = []
    
    with open(csv_path, mode='r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            doc = {
                "panel_id": parse_string(row.get("panel_id")),
                "panel_name": parse_string(row.get("panel_name")),
                "panel_type": parse_string(row.get("panel_type")),
                "version": parse_string(row.get("version")),
                "status": parse_string(row.get("status")),
                "target_genes": parse_array(row.get("target_genes")),
                "turnaround_days": parse_int(row.get("turnaround_days")),
                "ordering_sites": parse_array(row.get("ordering_sites")),
                "manufacturer": parse_string(row.get("manufacturer")),
                "regulatory_clearance": parse_string(row.get("regulatory_clearance")),
                "clinical_utility": parse_string(row.get("clinical_utility")),
                "created_at": parse_string(row.get("created_at"))
            }
            documents.append(doc)
    if documents:
        collection.insert_many(documents)
        print(f"successfully import {len(documents)} documents into gene_panels collection")

#! ingest collection 3: variants
def ingest_variants(csv_path="data/pgx_variants.csv"):
    collection = db["variants"]
    collection.delete_many({})
    documents = []
    
    with open(csv_path, mode='r', encoding='utf-8') as file:
        reader = csv.DictReader()
        for row in reader:
            doc = {
                "variant_id": parse_string(row.get("variant_id")),
                "panel_id": parse_string(row.get("panel_id")),
                "gene_symbol": parse_string(row.get("gene_symbol")),
                "hgvs_notation": parse_string(row.get("hgvs_notation")),
                "rsid": parse_string(row.get("rsid")),
                "chromosome": str(row.get("chromosome")).strip() if row.get("chromosome") else None,
                "position": parse_int(row.get("position")),
                "ref_allele": parse_string(row.get("ref_allele")),
                "alt_allele": parse_string(row.get("alt_allele")),
                "variant_type": parse_string(row.get("variant_type")),
                "zygosity_expected": parse_string(row.get("zygosity_expected")),
                "clinical_significance": parse_string(row.get("clinical_significance")),
                "associated_condition": parse_string(row.get("associated_condition")),
                "inheritance_pattern": parse_string(row.get("inheritance_pattern")),
                "evidence_level": parse_string(row.get("evidence_level")),
                "created_at": parse_string(row.get("created_at"))
            }
            documents.append(doc)
    if documents:
        collection.insert_many(documents)
        print(f"successfully import {len(documents)} documents into variants collection")
        
#! ingest collection 4: drug_responses
def ingest_drug_responses(csv_path="data/pgx_drug_responses.csv"):
    collection = db["drug_responses"]
    collection.delete_many()
    documents = []
    
    with open(csv_path, mode='r', encoding='utf-8') as file:
        reader = csv.DictReader()
        for row in reader:
            doc = {
                "response_id": parse_string(row.get("response_id")),
                "patient_id": parse_string(row.get("patient_id")),
                "panel_id": parse_string(row.get("panel_id")),
                "variant_id": parse_string(row.get("variant_id")),
                "drug_name": parse_string(row.get("drug_name")),
                "drug_class": parse_string(row.get("drug_class")),
                "response_type": parse_string(row.get("response_type")),
                "outcome": parse_string(row.get("outcome")),
                "phenotype_observed": parse_string(row.get("phenotype_observed")),
                "ctcae_grade": parse_int(row.get("ctcae_grade")),
                "recommendation": parse_string(row.get("recommendation")),
                "evidence_source": parse_string(row.get("evidence_source")),
                "reported_at": parse_string(row.get("reported_at")),
                "reported_on": parse_string(row.get("reported_on")),
                "created_at": parse_string(row.get("created_at"))
            }
            if doc["ctcae_grade"] is None:
                del doc["ctcae_grade"]
            documents.append(doc)
            
    if documents:
        collection.insert_many(documents)
        print(f"successfully import {len(documents)} documents into drug_responses collection")

#! call ingestion functions
ingest_patients()
ingest_gene_panels()
ingest_variants()
ingest_drug_responses()
client.close()