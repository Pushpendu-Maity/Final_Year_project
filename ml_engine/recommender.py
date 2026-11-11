import sqlite3
import os
import json
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ml_engine.data_mining import DiseaseClassifier, PatientClusterer

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'healthcare.db')

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

class CDSSRecommender:
    """
    Clinical Decision Support System (CDSS) & Healthcare Recommendation Engine.
    Analyzes patient symptoms, vitals, and relational medical history to generate:
    - Differential Diagnosis
    - Medications with Specific Indications, Dosages & Safety Contraindications
    - Evidence-Based Preventive Measures
    - Diagnostic Lab Test Suggestions
    - Specialist Doctor Profiles with Google Search URLs & clinic details
    """
    def __init__(self):
        self.classifier = DiseaseClassifier()
        self.classifier.train_and_evaluate()

    def generate_recommendations(self, active_symptoms, patient_vitals=None, medical_history=None):
        patient_vitals = patient_vitals or {}
        medical_history = medical_history or []

        # 1. Machine Learning Multi-Model Disease Prediction
        predictions = self.classifier.predict_disease(active_symptoms)

        if not predictions:
            primary_disease = "General Viral Syndrome"
            confidence = 60.0
        else:
            primary_disease = predictions[0]['disease']
            confidence = predictions[0]['probability']

        conn = get_db()
        cursor = conn.cursor()

        # Fetch Primary Disease Details
        disease_row = cursor.execute("SELECT id, name, category, description, icd10_code FROM diseases WHERE name = ?;", (primary_disease,)).fetchone()
        disease_id = disease_row['id'] if disease_row else None

        # 2. Risk Triage Calculation
        triage_level, red_flags = self._evaluate_triage(active_symptoms, patient_vitals)

        # 3. Dynamic Medication Recommendation Engine
        medications_list = []
        med_ids_added = set()

        # Step 3a: Add Primary Line-of-Treatment Medications from Database
        if disease_id:
            med_rows = cursor.execute("""
                SELECT m.id, m.name, m.category, m.standard_dosage, m.timing_instructions, m.contraindications, m.side_effects, dm.line_of_treatment, dm.efficacy_score
                FROM disease_medications dm
                JOIN medications m ON dm.medication_id = m.id
                WHERE dm.disease_id = ?
                ORDER BY dm.line_of_treatment ASC, dm.efficacy_score DESC;
            """, (disease_id,)).fetchall()

            for m in med_rows:
                safety_alert = self._check_contraindications(m, medical_history, patient_vitals)
                med_ids_added.add(m['id'])
                medications_list.append({
                    'id': m['id'],
                    'name': m['name'],
                    'category': m['category'],
                    'indication': f"Primary treatment for {primary_disease}",
                    'standard_dosage': m['standard_dosage'],
                    'timing_instructions': m['timing_instructions'] or "Take as directed with water.",
                    'line_of_treatment': f"Line {m['line_of_treatment']}",
                    'efficacy_score': f"{int(m['efficacy_score'] * 100)}%",
                    'side_effects': m['side_effects'],
                    'safety_alert': safety_alert
                })

        # Step 3b: Dynamic Symptom-Specific Supportive Relief Medications
        symptom_med_triggers = [
            # Fever relief
            (['SYM_041', 'SYM_011'], "Paracetamol (Acetaminophen) 650mg", "Symptomatic relief of fever and body aches"),
            # Epistaxis / Nose Bleeding relief
            (['SYM_043'], "Oxymetazoline 0.05% Nasal Spray", "Topical vasoconstrictor for active epistaxis (nose bleed)"),
            (['SYM_043'], "Tranexamic Acid 500mg", "Hemostatic agent for persistent nasal bleeding"),
            # Nausea & Vomiting relief
            (['SYM_020', 'SYM_049'], "Ondansetron 4mg", "Antiemetic for nausea and vomiting control"),
            # Diarrhea & Dehydration relief
            (['SYM_050'], "Oral Rehydration Salts (ORS World Health Org Formula)", "Essential electrolyte rehydration for fluid loss"),
            # Allergy & Runny Nose relief
            (['SYM_026', 'SYM_027', 'SYM_044'], "Montelukast 10mg + Levocetirizine 5mg", "Relief of acute rhinorrhea, sneezing and nasal blockage"),
            # Severe headache / body ache relief
            (['SYM_015', 'SYM_024'], "Ibuprofen 400mg", "Anti-inflammatory pain relief for acute headache and myalgia")
        ]

        for trigger_syms, med_name_target, indication_reason in symptom_med_triggers:
            if any(s in active_symptoms for s in trigger_syms):
                med_row = cursor.execute("""
                    SELECT id, name, category, standard_dosage, timing_instructions, contraindications, side_effects
                    FROM medications WHERE name = ?;
                """, (med_name_target,)).fetchone()
                
                if med_row and med_row['id'] not in med_ids_added:
                    safety_alert = self._check_contraindications(med_row, medical_history, patient_vitals)
                    med_ids_added.add(med_row['id'])
                    medications_list.append({
                        'id': med_row['id'],
                        'name': med_row['name'],
                        'category': med_row['category'],
                        'indication': indication_reason,
                        'standard_dosage': med_row['standard_dosage'],
                        'timing_instructions': med_row['timing_instructions'] or "Take as directed with water.",
                        'line_of_treatment': "Supportive Care",
                        'efficacy_score': "95%",
                        'side_effects': med_row['side_effects'],
                        'safety_alert': safety_alert
                    })

        # 4. Evidence-Based Preventive Measures
        preventive_measures = []
        if disease_id:
            prev_rows = cursor.execute("""
                SELECT measure_type, description, priority
                FROM preventive_measures
                WHERE disease_id = ?
                ORDER BY CASE priority WHEN 'Critical' THEN 1 WHEN 'High' THEN 2 ELSE 3 END;
            """, (disease_id,)).fetchall()

            for p in prev_rows:
                preventive_measures.append({
                    'type': p['measure_type'],
                    'description': p['description'],
                    'priority': p['priority']
                })

        # 5. Diagnostic Investigations & Tests
        category_name = disease_row['category'] if disease_row else 'General'
        lab_tests = self._recommend_lab_tests(category_name, active_symptoms, patient_vitals)

        # 6. Specialist Doctor Matching (with Google query link and rich profile)
        specialists = []
        cat_search = f"%{category_name}%"
        
        # Determine preferred specialty
        specialty_priority = {
            'Cardiovascular': 'Cardiology',
            'Endocrine': 'Endocrinology',
            'Respiratory': 'Pulmonology',
            'Gastrointestinal': 'Gastroenterology',
            'Neurological': 'Neurology',
            'Orthopedic': 'Rheumatology',
            'Renal': 'Nephrology',
            'Psychiatric': 'Psychiatry',
            'Infectious': 'Internal Medicine',
            'Dermatological': 'Dermatology',
            'ENT': 'ENT',
            'Urological': 'Urology'
        }.get(category_name, 'Internal Medicine')

        doc_rows = cursor.execute("""
            SELECT id, name, qualifications, specialty, hospital, experience_years, rating, reviews_count, consultation_fee, timings, location, contact, google_query_url, bio
            FROM doctor_specialists
            WHERE specialty = ? OR specialty LIKE ? OR specialty = 'Internal Medicine'
            ORDER BY CASE WHEN specialty = ? THEN 1 ELSE 2 END, rating DESC
            LIMIT 4;
        """, (specialty_priority, cat_search, specialty_priority)).fetchall()

        for d in doc_rows:
            specialists.append({
                'id': d['id'],
                'name': d['name'],
                'qualifications': d['qualifications'],
                'specialty': d['specialty'],
                'hospital': d['hospital'],
                'experience': f"{d['experience_years']} Years Experience",
                'rating': d['rating'],
                'reviews_count': d['reviews_count'],
                'consultation_fee': d['consultation_fee'],
                'timings': d['timings'],
                'location': d['location'],
                'contact': d['contact'],
                'google_query_url': d['google_query_url'],
                'bio': d['bio']
            })

        conn.close()

        return {
            'diagnosis': {
                'primary_disease': primary_disease,
                'confidence': confidence,
                'category': disease_row['category'] if disease_row else 'General Medicine',
                'icd10_code': disease_row['icd10_code'] if disease_row else 'R69',
                'description': disease_row['description'] if disease_row else 'Clinical presentation requiring diagnostic evaluation.',
                'differential': predictions
            },
            'triage': {
                'level': triage_level['level'],
                'color': triage_level['color'],
                'badge': triage_level['badge'],
                'message': triage_level['message'],
                'red_flags': red_flags
            },
            'medications': medications_list,
            'preventive_measures': preventive_measures,
            'diagnostic_tests': lab_tests,
            'specialists': specialists
        }

    def _evaluate_triage(self, symptoms, vitals):
        red_flags = []
        bp_sys = vitals.get('bp_sys', 120)
        glucose = vitals.get('glucose', 90)

        # Cardiac red flags
        if 'SYM_001' in symptoms and 'SYM_002' in symptoms:
            red_flags.append("Acute Chest Pain combined with Shortness of Breath (Potential Acute Coronary Syndrome)")
        # Fever & respiratory red flags
        if 'SYM_011' in symptoms and 'SYM_002' in symptoms:
            red_flags.append("High Grade Fever (>101°F) with Respiratory Distress / Breathlessness")
        # Persistent epistaxis red flag
        if 'SYM_043' in symptoms and bp_sys >= 150:
            red_flags.append("Active Epistaxis (Nose Bleed) accompanied by Elevated Blood Pressure (Hypertensive Epistaxis)")
        # Severe dehydrating gastroenteritis
        if 'SYM_049' in symptoms and 'SYM_050' in symptoms:
            red_flags.append("Concurrent Vomiting and Watery Diarrhea (Risk of Rapid Hypovolemic Dehydration)")
        # BP crises
        if bp_sys >= 180:
            red_flags.append(f"Hypertensive Crisis Alert: Systolic BP is critically high at {bp_sys} mmHg")
        if glucose >= 250:
            red_flags.append(f"Severe Hyperglycemia Alert: Random Blood Glucose is {glucose} mg/dL")

        if len(red_flags) > 0 or bp_sys >= 180:
            level = {
                'level': 'Emergency',
                'color': '#ef4444',
                'badge': 'CRITICAL / EMERGENCY TRIAGE',
                'message': 'Immediate clinical evaluation and emergency medical attention required.'
            }
        elif bp_sys >= 140 or glucose >= 160 or len(symptoms) >= 4:
            level = {
                'level': 'Urgent',
                'color': '#f59e0b',
                'badge': 'URGENT CLINICAL ASSESSMENT',
                'message': 'Prompt physician consultation recommended within 24 to 48 hours.'
            }
        else:
            level = {
                'level': 'Routine',
                'color': '#10b981',
                'badge': 'ROUTINE PRELIMINARY ASSESSMENT',
                'message': 'Standard outpatient consultation and personalized preventive measures recommended.'
            }

        return level, red_flags

    def _check_contraindications(self, med_row, medical_history, vitals):
        hist_str = ' '.join(medical_history).lower()
        med_name = (med_row['name'] if isinstance(med_row, dict) else med_row['name']).lower()
        med_cat = (med_row['category'] if isinstance(med_row, dict) else med_row['category']).lower()
        contra_str = ((med_row['contraindications'] or '') if isinstance(med_row, dict) else (med_row['contraindications'] or '')).lower()

        # Penicillin Allergy
        if ('penicillin' in hist_str or 'amox' in hist_str) and ('penicillin' in med_cat or 'amoxicillin' in med_name or 'augmentin' in med_name):
            return "CRITICAL ALLERGY ALERT: Patient has reported Penicillin Drug Allergy!"

        # Sulfa Allergy
        if 'sulfa' in hist_str and ('glimepiride' in med_name or 'sulfonylurea' in med_cat):
            return "CONTRAINDICATION: Patient has Sulfa allergy; risk of cross-reactivity with sulfonylureas."

        # Aspirin / NSAID sensitivity
        if ('aspirin' in hist_str or 'nsaid' in hist_str) and ('aspirin' in med_name or 'ibuprofen' in med_name or 'meloxicam' in med_name):
            return "WARNING: Patient has reported NSAID/Aspirin sensitivity or gastric risk."

        # Asthma & Beta Blockers / NSAIDs
        if 'asthma' in hist_str and ('ibuprofen' in med_name or 'aspirin' in med_name):
            return "CAUTION: NSAIDs can trigger bronchospasm in patients with chronic asthma."

        # Chronic Kidney Disease
        if ('kidney' in hist_str or 'renal' in hist_str) and ('ibuprofen' in med_name or 'meloxicam' in med_name or 'ciprofloxacin' in med_name):
            return "RENAL CAUTION: Adjust dose or avoid NSAID/nephrotoxic agent due to renal history."

        # Hypotension
        if vitals.get('bp_sys', 120) < 95 and ('amlodipine' in med_name or 'telmisartan' in med_name or 'lisinopril' in med_name):
            return "WARNING: Patient is hypotensive (Systolic BP < 95 mmHg)."

        # Epistaxis & Antiplatelet
        if 'epistaxis' in hist_str and 'aspirin' in med_name:
            return "CAUTION: Antiplatelet therapy increases risk and duration of nasal hemorrhage."

        return None

    def _recommend_lab_tests(self, category, symptoms, vitals):
        tests = []
        cat_lower = category.lower()

        if 'cardio' in cat_lower or 'SYM_001' in symptoms or vitals.get('bp_sys', 120) >= 140:
            tests.append({'name': '12-Lead Electrocardiogram (ECG)', 'purpose': 'Evaluate cardiac rhythm, ST-T waves, ischemia, and chamber hypertrophy.', 'urgency': 'High'})
            tests.append({'name': 'Lipid Profile Panel', 'purpose': 'Measure Total Cholesterol, LDL, HDL, and Triglycerides.', 'urgency': 'High'})

        if 'endo' in cat_lower or 'SYM_006' in symptoms or vitals.get('glucose', 90) >= 126:
            tests.append({'name': 'Fasting Plasma Glucose & HbA1c', 'purpose': 'Assess chronic glycemic control and diabetes staging.', 'urgency': 'High'})

        if 'resp' in cat_lower or 'SYM_002' in symptoms or 'SYM_009' in symptoms or 'SYM_047' in symptoms:
            tests.append({'name': 'Chest X-Ray (PA View)', 'purpose': 'Detect pulmonary consolidation, infiltrates, or hyperinflation.', 'urgency': 'High'})

        if 'ent' in cat_lower or 'SYM_043' in symptoms:
            tests.append({'name': 'Complete Hemogram (CBC) & Platelet Count', 'purpose': 'Screen for thrombocytopenia, anemia, or coagulopathy in epistaxis.', 'urgency': 'High'})
            tests.append({'name': 'Prothrombin Time (PT/INR) & aPTT', 'purpose': 'Evaluate blood clotting cascade and hemostatic efficiency.', 'urgency': 'Medium'})

        if 'gastro' in cat_lower or 'SYM_049' in symptoms or 'SYM_050' in symptoms:
            tests.append({'name': 'Serum Electrolytes (Na+, K+, Cl-)', 'purpose': 'Assess electrolyte depletion and dehydration secondary to diarrhea/vomiting.', 'urgency': 'High'})

        if not tests:
            tests.append({'name': 'Complete Blood Count (CBC) with Differential', 'purpose': 'Screen for leukocytosis, infection, and red cell counts.', 'urgency': 'Routine'})
            tests.append({'name': 'Basic Metabolic Panel (BMP)', 'purpose': 'Measure kidney function (BUN/Creatinine) and serum glucose.', 'urgency': 'Routine'})

        return tests

if __name__ == '__main__':
    recommender = CDSSRecommender()
    res = recommender.generate_recommendations(
        active_symptoms=['SYM_043', 'SYM_044', 'SYM_045'],
        patient_vitals={'bp_sys': 148, 'glucose': 110, 'bmi': 26.2},
        medical_history=['Recurrent Nose Bleeding (Epistaxis)', 'Penicillin Drug Allergy']
    )
    print("Diagnosis:", res['diagnosis'])
    print("Meds Count:", len(res['medications']))
    print("Meds:", [m['name'] for m in res['medications']])
    print("Specialists:", [d['name'] for d in res['specialists']])
