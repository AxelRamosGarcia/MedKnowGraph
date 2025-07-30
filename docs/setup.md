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
