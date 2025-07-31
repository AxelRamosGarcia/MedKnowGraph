# src/chatbot_logic.py (Conceptual)

import kg_query_manager as kgm # Our Neo4j query functions

def run_medical_chatbot():
    print("Hello! I am MedKnowGraph, your medical symptom assistant. Please describe your main symptom.")
    user_symptoms = []
    conversation_history = [] # To keep track of what user said

    while True:
        user_input = input("\nYou: ").strip()
        conversation_history.append({"role": "user", "text": user_input})

        # Step 1: Extract initial symptom (simple for now, later NLP)
        # For prototype, assume first user input is a primary symptom
        current_symptom_input = user_input.lower()

        # Add to list of all symptoms provided by user so far
        user_symptoms.append(current_symptom_input)

        # Step 2: Query KG for initial diagnoses or refined diagnoses
        if len(user_symptoms) == 1:
            # First symptom: Use get_initial_diagnoses
            results = kgm.get_initial_diagnoses(current_symptom_input)
            # LLM call here with results for initial response
            # Example: LLM_response = generate_initial_response(user_input, results)
            # print("MedKnowGraph (LLM):", LLM_response)
            print("\nMedKnowGraph (Logic): Based on your first symptom, here are some initial thoughts...")
            if results:
                for record in results:
                    print(f"- {record['PotentialDiagnosis']} (Level: {record['SymptomLevel']})")
                # For simplicity, pick the top diagnosis to ask follow-up symptoms
                top_diagnosis = results[0]['PotentialDiagnosis']
                # LLM_response for follow up based on related symptoms
                # related_symptoms = kgm.get_related_symptoms(top_diagnosis, user_symptoms)
                # Example: LLM_follow_up = generate_follow_up_questions(top_diagnosis, related_symptoms)
                # print("MedKnowGraph (LLM Follow-up):", LLM_follow_up)
                print(f"To help narrow it down, are you experiencing any other symptoms commonly associated with {top_diagnosis}?")
            else:
                print("I couldn't find any direct matches for that symptom in my knowledge base. Can you describe it differently?")

        else:
            # Subsequent symptoms: Use refine_diagnosis_by_multiple_symptoms
            results = kgm.refine_diagnosis_by_multiple_symptoms(user_symptoms)
            print("\nMedKnowGraph (Logic): With your additional symptoms, here's a refined list...")
            if results:
                for record in results:
                    print(f"- {record['RefinedDiagnosis']} (Matches {record['numMatchedSymptoms']} of your symptoms)")
                # LLM_response = generate_final_diagnosis_summary(user_symptoms, results)
                # print("MedKnowGraph (LLM):", LLM_response)
                print("Remember, this is for informational purposes only. Please consult a medical professional.")
            else:
                print("With those symptoms, I'm having trouble finding a clear match. Do you have any other symptoms?")

        # Add a condition to exit
        if "quit" in user_input.lower() or "exit" in user_input.lower():
            print("Thank you for using MedKnowGraph. Goodbye!")
            break

if __name__ == "__main__":
    run_medical_chatbot()
    kgm.close_driver()
