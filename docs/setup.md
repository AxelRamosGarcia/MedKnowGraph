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
