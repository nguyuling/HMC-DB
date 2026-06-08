# Helix-Medical-Center-DB
**SECB3213 Bioinformatics Database Mini Project**

## Team Members
| No. | Name | Metric No. |
| --- | --- | --- |
| 1. | ALDANISHA MUADZ BINTI MUZAFFAR | A23CS0039 |
| 2. | CHUA SHANG YEET | |
| 3. | NGU YU LING | A23CS0149 |


## Raw Data Files
```
data-case-pgx/
```
| No. | File | Shape (Exc. header row) | Description |
| --- | --- | --- | --- |
| 1. | **`pgx_drug_response.csv`** | (200, 15) | Patient ID, drug info, outcome, phenotype observed etc. |
| 2. | **`pgx_gene_panels.csv`** | (9, 12) | Panel info, target genes, manufacturer etc. |
| 3. | **`pgx_patients.csv`** | (100, 15) | Patient basic info, medical info |
| 4. | **`pgx_variants.csv`** | (40, 16) | Gene, chromosome, allelic variants etc. |


## Deliverables
| No. | Deliverables | File | Description |
| --- | --- | --- | --- |
| D1 | MongoDB Schema Design | **`schema.json`** | Structure Design of the solution |
| D2 | Data Ingestion Code | **`data.py`** | PyMongo ingestion script that connects to MongoDB |
| D3 | Database Backup | **`dump.tar.gz`** | MongoDump archive of the populated data |
| D4 | Query & Result | **`query.py`** & `results.pdf` | MongoDB queries and 10 results |
| D5 | FastAPI Implementation | **`api.py`** | All 10 API endpoints |
| D6 | Data Portal | **`portal.py`** | Read-only interactive portal using Streamlit |
| D7 | Technical Report | **`report.pdf`** | Report that outlines the mini project |
| D8 | System Demostration Video | **`demo.mp4`** | Presentation video of the portal | 