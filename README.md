## Helix Medical Center Data Portal
This is a Mini Project for the course SECB3213 Bioinformatics Database.

- **Group 3 Team Members:**
    | No. | Name | Metric No. |
    | --- | --- | --- |
    | 1. | ALDANISHA MUADZ BINTI MUZAFFAR | A23CS0039 |
    | 2. | CHUA SHANG YEET | A23CS0297 |
    | 3. | NGU YU LING | A23CS0149 |

- **Mini Project Deliverables:**
    | No. | Deliverables | Files | Description |
    | --- | --- | --- | --- |
    | D1 | MongoDB Schema Design | **`D1_schemas`** | Structure Design of the solution |
    | D2 | Data Ingestion Code | **`D2_ingestion.py`** | PyMongo ingestion script that connects to MongoDB |
    | D3 | Database Backup | **`D3_backup.tar.gz`** | MongoDump archive of the populated data |
    | D4 | Query & Result | **`D4_query.py`** & `results.pdf` | MongoDB queries and 10 results |
    | D5 | FastAPI Implementation | **`D5_api.py`** | All 10 API endpoints |
    | D6 | Data Portal | **`D6_portal.py`** | Read-only interactive portal using Streamlit |
    | D7 | Technical Report | **`D7_report.pdf`** | Report that outlines the mini project |
    | D8 | System Demostration Video | **`D8_video.mp4`** | Presentation video of the portal | 


## D1 — MongoDB Schema Design
- **Entity-Relationship Diagram (ERD)**
    ![ERD](data/erd.png)

- **Schema Design of all 4 entities:**
    - string: `"attribute": { "type": "string" }`
    - array: `"attribute": { "type": "array", "items": { "type": "string" } }`
    - integer: `"attribute": { "type": "integer" }`
    - date: `"attribute": { "type": "string", "format": "date" }`


## D2 — Data Ingestion Code
- **Overview of Data in `data/xxx.csv`:**
    | No. | Files | Shape (Exc. header row) | Description |
    | --- | --- | --- | --- |
    | 1. | **`pgx_patients.csv`** | (100, 15) | Patient basic info, medical info |
    | 2. | **`pgx_gene_panels.csv`** | (9, 12) | Panel info, target genes, manufacturer etc. |
    | 3. | **`pgx_variants.csv`** | (40, 16) | Gene, chromosome, allelic variants etc. |
    | 4. | **`pgx_drug_response.csv`** | (200, 15) | Patient ID, drug info, outcome, phenotype observed etc. |

- Step in Data Ingestion:
    - In MongoDB Atlas, create a project `HelixMedicalCenter` -> cluster `cluster0` -> database `HMC`
    - Using pymongo (in .py file), establish MongoDB connection
    - define functions `parse_array()`, `parse_int()`, `parse_string()`
    - for each of the 4 entities, define a collection, read the csv file, insert each row of csv as a document into the collection


## D3 — Database Backup  
- Install the MongoDB Database Tools suite using `brew install mongodb-database-tools` (for MacOS)
- Run mongodump in terminal: 
```
    mongodump --uri="mongodb+srv://dbAdmin:<password>@cluster0.iuvvkqs.mongodb.net/HMC" --archive=hmc_backup.tar.gz --gzip
```


## D4 — Queries & Results

## D5 — FastAPI Implementation 

## D6 — Data Portal

## D7 — Technical Report

## D8 — System Demonstration Video
