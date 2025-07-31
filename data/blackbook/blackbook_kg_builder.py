# src/blackbook_kg_builder.py
import pandas as pd
import os

# --- Configuration ---
BLACKBOOK_INPUT_PATH = '/mnt/nfs/gluster_brick/AARG/MedKnowGraph/Black_book/KG_DataBase.csv' # Adjust filename if different
OUTPUT_NODES_DIR = '/mnt/nfs/gluster_brick/AARG/MedKnowGraph/Black_book'
OUTPUT_RELATIONSHIPS_DIR = '/mnt/nfs/gluster_brick/AARG/MedKnowGraph/Black_book'

os.makedirs(OUTPUT_NODES_DIR, exist_ok=True)
os.makedirs(OUTPUT_RELATIONSHIPS_DIR, exist_ok=True)

def clean_text(text):
    """Removes common non-alphanumeric chars and ensures string type."""
    if pd.isna(text):
        return None
    text = str(text).replace('"', '').replace("'", "").strip()
    # Further cleaning if specific characters are observed in the data
    return text if text else None

print(f"Loading Blackbook data from: {BLACKBOOK_INPUT_PATH}")
try:
    df_blackbook = pd.read_csv(BLACKBOOK_INPUT_PATH)
except FileNotFoundError:
    print(f"Error: Blackbook CSV not found at {BLACKBOOK_INPUT_PATH}. Please check the path.")
    exit()

print(f"Original Blackbook data shape: {df_blackbook.shape}")
print("Columns available:", df_blackbook.columns.tolist())


# --- Extract Diagnosis Nodes ---
print("Extracting Diagnosis Nodes...")
diagnoses = df_blackbook[['Diagnosis_(DX)', 'Diagnosis_(DX)_Notes', 'General_Notes', 'Life_Threatening', 'Definitions']].copy()
diagnoses.columns = ['name', 'notes', 'general_notes', 'life_threatening', 'definitions']
diagnoses['name'] = diagnoses['name'].apply(clean_text)
diagnoses = diagnoses.dropna(subset=['name']).drop_duplicates(subset=['name'])
diagnoses['id'] = 'D_' + (diagnoses.index + 1).astype(str) # Generate unique IDs
diagnoses['type'] = 'Diagnosis'
diagnoses_nodes = diagnoses[['id', 'name', 'type', 'notes', 'general_notes', 'life_threatening', 'definitions']]
diagnoses_nodes.to_csv(os.path.join(OUTPUT_NODES_DIR, 'blackbook_diagnosis_nodes.csv'), index=False)
print(f"Extracted {len(diagnoses_nodes)} unique Diagnosis nodes.")


# --- Extract Symptom Nodes and Symptom-Diagnosis Relationships ---
print("Extracting Symptom Nodes and Relationships...")
symptom_data = [] # To collect all symptoms
relationships = [] # To collect all relationships

# Map diagnosis names to their generated IDs for relationships
diagnosis_name_to_id = diagnoses.set_index('name')['id'].to_dict()

# Iterate through each row to get symptoms and create relationships
for idx, row in df_blackbook.iterrows():
    dx_name = clean_text(row['Diagnosis_(DX)'])
    if dx_name is None or dx_name not in diagnosis_name_to_id:
        continue # Skip if diagnosis is invalid or not in our extracted list

    dx_id = diagnosis_name_to_id[dx_name]

    # Extract Chief_Sign
    chief_sign = clean_text(row['Chief_Sign'])
    if chief_sign:
        symptom_data.append({'name': chief_sign, 'type': 'Symptom'})
        relationships.append({
            'source_name': chief_sign,
            'source_type': 'Symptom',
            'relationship_type': 'INDICATES',
            'target_id': dx_id,
            'target_name': dx_name,
            'target_type': 'Diagnosis',
            'level': 'Chief Sign',
            'notes': clean_text(row['Cheif_Sign_Notes'])
        })

    # Extract Level_1 to Level_10 Symptoms
    for i in range(1, 11):
        level_col = f'Level_{i}'
        notes_col = f'Level_{i}_Notes'

        symptom_text = clean_text(row.get(level_col))
        if symptom_text:
            symptom_data.append({'name': symptom_text, 'type': 'Symptom'})
            relationships.append({
                'source_name': symptom_text,
                'source_type': 'Symptom',
                'relationship_type': 'INDICATES',
                'target_id': dx_id,
                'target_name': dx_name,
                'target_type': 'Diagnosis',
                'level': f'Level {i}',
                'notes': clean_text(row.get(notes_col))
            })

# Create Symptom Nodes DataFrame
symptom_nodes = pd.DataFrame(symptom_data).drop_duplicates(subset=['name'])
symptom_nodes['id'] = 'S_' + (symptom_nodes.index + 1).astype(str) # Generate unique IDs
symptom_nodes.to_csv(os.path.join(OUTPUT_NODES_DIR, 'blackbook_symptom_nodes.csv'), index=False)
print(f"Extracted {len(symptom_nodes)} unique Symptom nodes.")

# Create Relationships DataFrame
# Replace symptom names with their generated IDs for relationship file
symptom_name_to_id = symptom_nodes.set_index('name')['id'].to_dict()
df_relationships = pd.DataFrame(relationships)
df_relationships['source_id'] = df_relationships['source_name'].map(symptom_name_to_id)

# Reorder columns for clarity in relationship CSV
final_relationships = df_relationships[[
    'source_id', 'source_type', 'relationship_type', 'target_id', 'target_type',
    'level', 'notes'
]].copy()

final_relationships.to_csv(os.path.join(OUTPUT_RELATIONSHIPS_DIR, 'blackbook_symptom_diagnosis_relationships.csv'), index=False)
print(f"Extracted {len(final_relationships)} Symptom-Diagnosis relationships.")

print("\nBlackbook KG build complete. Check 'data/extracted_kg_prototype/blackbook_nodes/' and '.../blackbook_relationships/'")
