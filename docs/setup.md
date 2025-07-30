# Day 1 - Environment Setup and MIMIC III Data Loading

## Project: MedKnowGraph - AI Assistant for Medical Symptom Analysis

This document outlines the essential tasks for Day 1 of the MedKnowGraph project, focusing on preparing your development environment and populating the MIMIC-III clinical database. This foundational step is crucial for building our medical knowledge graph and enabling subsequent AI functionalities.

### Prerequisites

Before starting, ensure the following are installed and accessible on your system:

* **Git:** For cloning the project repository.
* **Python 3.10+:** With `venv` (virtual environment) support.
    * Verify: `python3 --version` (e.g., `Python 3.11.7`)
* **PostgreSQL 14+:** The relational database system.
    * Verify: `psql --version` (e.g., `psql (PostgreSQL) 14.18`)
* **`gunzip`:** Standard utility for decompressing `.gz` files (typically pre-installed on Linux).
* **MIMIC-III Data (version 1.4 recommended):** The complete dataset (`.csv.gz` files) downloaded from PhysioNet. Access requires formal approval and completion of necessary training/agreements from PhysioNet.

**Basic Dependency Installation (Example for Ubuntu/Debian):**

```bash
# Update package lists
sudo apt update

# Install essential development tools, Python components, and PostgreSQL
sudo apt install -y \
  build-essential \
  git \
  curl \
  wget \
  python3.11 python3.11-venv python3-pip \
  postgresql postgresql-contrib \
  libpq-dev # Required for psycopg2-binary
```
## Project Setup and Python Virtual Environment

Begin by setting up your project directory and a dedicated Python environment.

### 1. Clone the MedKnowGraph repository:
```bash
git clone https://github.com/AxelRamosGarcia/MedKnowGraph.git
cd MedKnowGraph
```

### 2. Create and activate a Python virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate # On Windows, use `venv\Scripts\activate`
```

### 3. Install core Python dependencies:
```bash
pip install psycopg2-binary pandas sqlalchemy
```
## PostgreSQL Configuration for MIMIC-III

Configure PostgreSQL instance to host MIMIC-III database.

### 1. Create a PstrfeSQL User and Database
This establishes a dedicated user (`mimic_user`) and database (`mimic`) for MIMIC-III
```bash
sudo -u postgres psql <<EOF
-- Crear rol y contraseña
CREATE ROLE mimic_user WITH LOGIN PASSWORD 'password';
-- Crear base de datos
CREATE DATABASE mimic OWNER mimic_user;
\q
EOF
```

### 2. Adjust PstgreSQL Client Authentication (`pg_hba.conf`):

This critical step allosw `mimic_user` to connect to the database witha  password, resolving "Peer authentication failed" errors.

#### a) Locate `pg_hba.conf`:
Determine the exact path to your PostgreSQL configuration file:
`bash sudo -u postgres psql -c "SHOW hba_file;" # Example output: /etc/postgresql/14/main/pg_hba.conf`

#### b) Edit the configuration file:
`bash sudo nano /path/to/your/pg_hba.conf # Replace with the actual path found above`

#### c) Modify or add authentication rules:
Locate the line `local all all peer` and change peer to md5. This enables password authentication for all local Unix sockets connections.

```diff
--- a/pg_hba.conf
+++ b/pg_hba.conf
@@ -20,7 +20,7 @@

 # "local" is for Unix domain socket connections only
 local   all             all                                     peer
+# Modified for password authentication for all local connections via Unix socket:
+local   all             all                                     md5
 # IPv4 local connections:
 host    all             all             127.0.0.1/32            scram-sha-256
 # IPv6 local connections:
```
Ensure the `host mimic mimic_user 127.0.0.1/32 md5` rule you added previously (for TCP/IP connections) is also present in this file.

#### d) Save changes and restart PostgreSQL service:
`bash # In nano: Press Ctrl+X, then Y (for Yes), then Enter to save. sudo systemctl restart postgresql`

## Load MIMIC-III Data into Databse
This is the most time-consuming set of Day 1, involving scheme creation, data ingestion, indexing, and constraint application using the official MIMIC-III scripts.

#### a) Create a shell script (`mimic_build.sh`):
Create a file in your MedKnowGraph project root it automates the entire loading process.
```bash
#!/bin/bash

# --- Configuration for Database Connection ---
export PGPASSWORD="Password" # Your actual password
export PGUSER="mimic_user"
export PGDATABASE="mimic"

# --- Paths to MIMIC-III Data and Build Scripts ---
MIMIC_BUILD_SCRIPTS_PATH="/mnt/nfs/gluster_brick/AARG/MedKnowGraph/mimic-code/mimic-iii/buildmimic/postgres/"
MIMIC_DATA_FILES_PATH="/mnt/nfs/gluster_brick/AARG/MedKnowGraph/physionet.org/files/mimiciii/1.4/"

echo "--- Step 1: Creating MIMIC-III tables ---"
# This creates the empty table structures.
psql -f "${MIMIC_BUILD_SCRIPTS_PATH}postgres_create_tables.sql"

echo ""
echo "--- Step 2: Loading data from gzipped CSV files ---"
# This populates the tables from your downloaded .csv.gz files.
# The script uses a psql variable 'mimic_data_dir' to find the data files.
psql -c "\set mimic_data_dir '${MIMIC_DATA_FILES_PATH}'" -f "${MIMIC_BUILD_SCRIPTS_PATH}postgres_load_data_gz.sql"

echo ""
echo "--- Step 3: Adding Indexes (Essential for Query Performance) ---"
# This step creates database indexes, significantly speeding up data retrieval.
psql -f "${MIMIC_BUILD_SCRIPTS_PATH}postgres_add_indexes.sql"

echo ""
echo "--- Step 4: Adding Constraints (Essential for Data Integrity) ---"
# This applies primary and foreign key constraints, ensuring data consistency.
psql -f "${MIMIC_BUILD_SCRIPTS_PATH}postgres_add_constraints.sql"

echo ""
echo "--- Verification: Check Data Counts ---"
# Run these queries to confirm that data has been loaded successfully into key tables.
psql -c "SELECT COUNT(*) FROM patients;"
psql -c "SELECT COUNT(*) FROM admissions;"
psql -c "SELECT COUNT(*) FROM diagnoses_icd;"
psql -c "SELECT COUNT(*) FROM d_icd_diagnoses;"
psql -c "SELECT COUNT(*) FROM prescriptions;"
psql -c "SELECT COUNT(*) FROM procedures_icd;"
psql -c "SELECT COUNT(*) FROM d_icd_procedures;"

echo ""
echo "MIMIC-III database setup and loading complete!"

# Unset environment variables for security (important!)
unset PGPASSWORD
unset PGUSER
unset PGDATABASE
```

#### b) Make the script executable:
```bash
chmod +x mimic_build.sh
```

#### c) Run the script within a `screen` session (Highly recommended):
The data loading and indexing process can take many hours (potentially 8-24+ hours depending on your system's I/O and CPU, especially on network-attached storage like NFS/GlusterFS). Using `screen` prevents disconnections from interrupting the process.
```bash
# 1. Start a new screen session:
screen

# 2. Inside the screen session, navigate to your project root:
cd /mnt/nfs/gluster_brick/AARG/MedKnowGraph/

# 3. Execute the build script:
./mimic_build.sh

# 4. Detach from the screen session:
#    Press Ctrl+A, then immediately press D.
#    You will see a message like "[detached from ...]".
#    You can now safely close your terminal or disconnect your SSH session.
```
To re-attach to the running session later (e.g., to check progress or troubleshoot):

```bash
screen -r
```
#### d) Initial Data Extraction for Knowledge Graph Prototype
Once the `mimic_build.sh` script has succesfully completed all its steps (i.e., you have verified data counts are non-zero after re-attaching to your `screen` session), you can proceed with extracting a foundational sbset of data.

##### Create the output directory:
```bash
mkdir -p data/extracted_kg_prototype
```
##### Review the extraction script (`src/data_extraction.py`):
Ensure the database connection details in this Python script match your `mimic_user`, `password`, and `mimic` database name.

```Python
# src/data_extraction.py (Excerpt for Database Configuration)
import pandas as pd
from sqlalchemy import create_engine
import os

DB_USER = os.getenv('DB_USER', 'mimic_user')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'EssRevanMIMICIII')
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_NAME = os.getenv('DB_NAME', 'mimic')

OUTPUT_DIR = 'data/extracted_kg_prototype'
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ... rest of the script, including SQL queries for data extraction and saving to CSVs
```

##### Run the data extraction script:
```bash
# Ensure your Python virtual environment is active
source venv/bin/activate

# (Optional, but good practice) Set environment variables if not directly hardcoded in script:
# export DB_USER='mimic_user'
# export DB_PASSWORD='EssRevanMIMICIII'
# export DB_NAME='mimic'

python src/data_extraction.py
```
Upon successful execution, this will generate CSV files (e.g., patient_diagnoses.csv, patient_medications.csv, diagnosis_procedures.csv) in your data/extracted_kg_prototype/ directory.
