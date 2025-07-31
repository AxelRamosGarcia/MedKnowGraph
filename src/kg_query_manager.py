import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- Neo4j Connection Details ---
# Retrieve from environment variables for security and flexibility
URI = os.getenv("NEO4J_URI", "bolt://localhost:7687") # Default to local
USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
PASSWORD = os.getenv("EssRevanMIMICIII") # IMPORTANT: Set this in your .env file

# Initialize the Neo4j driver
try:
    driver = GraphDatabase.driver(URI, auth=(USERNAME, PASSWORD))
    driver.verify_connectivity()
    print("Neo4j driver initialized and connected successfully!")
except Exception as e:
    print(f"Failed to connect to Neo4j: {e}")
    driver = None # Set driver to None if connection fails

def close_driver():
    if driver:
        driver.close()
        print("Neo4j driver closed.")

# --- Cypher Query Functions ---

def get_initial_diagnoses(symptom_text: str):
    if not driver:
        print("Error: Neo4j driver not connected.")
        return []
    query = """
    MATCH (s:Symptom)-[r:INDICATES]->(d:Diagnosis)
    WHERE toLower(s.name) CONTAINS toLower($symptom_text)
    RETURN s.name AS MatchedSymptom,
           d.name AS PotentialDiagnosis,
           r.level AS SymptomLevel,
           r.notes AS SymptomNotes,
           d.notes AS DiagnosisNotes,
           d.life_threatening AS IsLifeThreatening
    ORDER BY
        CASE r.level
            WHEN 'Chief Sign' THEN 1
            WHEN 'Level 1' THEN 2
            WHEN 'Level 2' THEN 3
            WHEN 'Level 3' THEN 4
            ELSE 99
        END, d.name
    LIMIT 10;
    """
    with driver.session() as session:
        result = session.run(query, symptom_text=symptom_text)
        return [record for record in result]

def get_related_symptoms(diagnosis_name: str, excluded_symptoms: list = []):
    if not driver:
        print("Error: Neo4j driver not connected.")
        return []
    # Use APOC if available and necessary for more complex list operations,
    # but for simple exclusion, Cypher's WHERE clause is sufficient.
    query = """
    MATCH (s:Symptom)-[r:INDICATES]->(d:Diagnosis)
    WHERE d.name = $diagnosis_name
      AND NOT toLower(s.name) IN [s.lower() | s IN $excluded_symptoms]
    RETURN s.name AS RelatedSymptom,
           r.level AS SymptomLevel,
           r.notes AS SymptomNotes
    ORDER BY
        CASE r.level
            WHEN 'Chief Sign' THEN 1
            WHEN 'Level 1' THEN 2
            WHEN 'Level 2' THEN 3
            WHEN 'Level 3' THEN 4
            ELSE 99
        END, s.name
    LIMIT 5;
    """
    with driver.session() as session:
        result = session.run(query, diagnosis_name=diagnosis_name, excluded_symptoms=excluded_symptoms)
        return [record for record in result]

def refine_diagnosis_by_multiple_symptoms(user_symptoms: list):
    if not driver:
        print("Error: Neo4j driver not connected.")
        return []
    query = """
    MATCH (s:Symptom)-[r:INDICATES]->(d:Diagnosis)
    WHERE any(symptom_text IN $user_symptoms WHERE toLower(s.name) CONTAINS toLower(symptom_text))

    WITH d, $user_symptoms AS userSymptoms, COLLECT({symptom: s.name, level: r.level}) AS associatedKGSymptoms

    WITH d, userSymptoms, associatedKGSymptoms,
         SIZE([symptom_text IN userSymptoms
               WHERE ANY(kg_symptom_map IN associatedKGSymptoms
                         WHERE toLower(kg_symptom_map.symptom) CONTAINS toLower(symptom_text))
               ]) AS numMatchedSymptoms

    WHERE numMatchedSymptoms > 0

    RETURN d.name AS RefinedDiagnosis,
           numMatchedSymptoms,
           [s IN associatedKGSymptoms | s.symptom] AS KGSymptomsForThisDiagnosis,
           d.notes AS DiagnosisNotes,
           d.life_threatening AS IsLifeThreatening
    ORDER BY numMatchedSymptoms DESC, d.name ASC
    LIMIT 5;
    """
    with driver.session() as session:
        result = session.run(query, user_symptoms=user_symptoms)
        return [record for record in result]

# --- Test Connection and Queries (optional, for direct testing) ---
if __name__ == "__main__":
    print("\n--- Testing Neo4j Connection and Queries ---")

    # Create .env file with your Neo4j password:
    # NEO4J_PASSWORD="your_neo4j_password_here"

    if driver:
        # Test get_initial_diagnoses
        print("\nInitial diagnoses for 'fever':")
        diagnoses = get_initial_diagnoses("fever")
        for diag in diagnoses:
            print(f"- {diag['PotentialDiagnosis']} (Level: {diag['SymptomLevel']}, Life-threatening: {diag['IsLifeThreatening']})")

        # Test get_related_symptoms
        if diagnoses:
            first_diagnosis = diagnoses[0]['PotentialDiagnosis']
            print(f"\nRelated symptoms for '{first_diagnosis}' (excluding 'fever'):")
            related_symptoms = get_related_symptoms(first_diagnosis, ["fever"])
            for symp in related_symptoms:
                print(f"- {symp['RelatedSymptom']} (Level: {symp['SymptomLevel']})")

        # Test refine_diagnosis_by_multiple_symptoms
        print("\nRefining diagnoses for 'headache', 'nausea', 'sensitivity to light':")
        refined_diagnoses = refine_diagnosis_by_multiple_symptoms(["headache", "nausea", "sensitivity to light"])
        for diag in refined_diagnoses:
            print(f"- {diag['RefinedDiagnosis']} (Matched: {diag['numMatchedSymptoms']} symptoms, KG Symptoms: {diag['KGSymptomsForThisDiagnosis']}, Life-threatening: {diag['IsLifeThreatening']})")
    else:
        print("Skipping query tests due to failed Neo4j connection.")

    close_driver()
