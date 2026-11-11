import sqlite3
import os
import random
import json

DB_PATH = os.path.join(os.path.dirname(__file__), 'healthcare.db')

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Enable foreign keys
    cursor.execute("PRAGMA foreign_keys = ON;")

    # 1. Patients Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS patients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        age INTEGER NOT NULL,
        gender TEXT NOT NULL,
        bmi REAL NOT NULL,
        blood_pressure_sys INTEGER NOT NULL,
        blood_pressure_dia INTEGER NOT NULL,
        glucose_level REAL NOT NULL,
        cholesterol REAL NOT NULL,
        smoking_status TEXT NOT NULL,
        activity_level TEXT NOT NULL,
        risk_category TEXT,
        diagnosed_condition TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    ''')

    # 2. Symptoms Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS symptoms (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        category TEXT NOT NULL,
        severity_weight REAL DEFAULT 1.0
    );
    ''')

    # 3. Diseases Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS diseases (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        category TEXT NOT NULL,
        description TEXT,
        icd10_code TEXT
    );
    ''')

    # 4. Disease Symptoms Junction Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS disease_symptoms (
        disease_id INTEGER NOT NULL,
        symptom_id INTEGER NOT NULL,
        weight REAL DEFAULT 1.0,
        is_primary INTEGER DEFAULT 0,
        PRIMARY KEY (disease_id, symptom_id),
        FOREIGN KEY (disease_id) REFERENCES diseases (id),
        FOREIGN KEY (symptom_id) REFERENCES symptoms (id)
    );
    ''')

    # 5. Medications Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS medications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        category TEXT NOT NULL,
        standard_dosage TEXT NOT NULL,
        timing_instructions TEXT,
        contraindications TEXT,
        side_effects TEXT
    );
    ''')

    # 6. Disease Medications Junction Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS disease_medications (
        disease_id INTEGER NOT NULL,
        medication_id INTEGER NOT NULL,
        line_of_treatment INTEGER DEFAULT 1,
        efficacy_score REAL DEFAULT 0.9,
        PRIMARY KEY (disease_id, medication_id),
        FOREIGN KEY (disease_id) REFERENCES diseases (id),
        FOREIGN KEY (medication_id) REFERENCES medications (id)
    );
    ''')

    # 7. Preventive Measures Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS preventive_measures (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        disease_id INTEGER NOT NULL,
        measure_type TEXT NOT NULL, -- Dietary, Lifestyle, Screening, Vaccine, Emergency
        description TEXT NOT NULL,
        priority TEXT DEFAULT 'Medium',
        FOREIGN KEY (disease_id) REFERENCES diseases (id)
    );
    ''')

    # 8. Patient Medical History Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS medical_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id INTEGER NOT NULL,
        condition_name TEXT NOT NULL,
        diagnosis_date TEXT NOT NULL,
        notes TEXT,
        FOREIGN KEY (patient_id) REFERENCES patients (id)
    );
    ''')

    # 9. Treatment Records Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS treatment_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id INTEGER NOT NULL,
        disease_id INTEGER NOT NULL,
        medication_id INTEGER NOT NULL,
        treatment_date TEXT NOT NULL,
        outcome TEXT NOT NULL, -- Recovered, Improved, No Change, Adverse Reaction
        side_effects_reported TEXT,
        FOREIGN KEY (patient_id) REFERENCES patients (id),
        FOREIGN KEY (disease_id) REFERENCES diseases (id),
        FOREIGN KEY (medication_id) REFERENCES medications (id)
    );
    ''')

    # 10. Doctor Specialists Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS doctor_specialists (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        qualifications TEXT NOT NULL,
        specialty TEXT NOT NULL,
        hospital TEXT NOT NULL,
        experience_years INTEGER NOT NULL,
        rating REAL NOT NULL,
        reviews_count INTEGER DEFAULT 150,
        consultation_fee TEXT NOT NULL,
        timings TEXT NOT NULL,
        location TEXT NOT NULL,
        contact TEXT NOT NULL,
        google_query_url TEXT,
        bio TEXT
    );
    ''')

    conn.commit()
    conn.close()
    print("Database tables initialized successfully.")

def seed_database(force_reseed=False):
    conn = get_db_connection()
    cursor = conn.cursor()

    if force_reseed:
        cursor.execute("DROP TABLE IF EXISTS treatment_records;")
        cursor.execute("DROP TABLE IF EXISTS medical_history;")
        cursor.execute("DROP TABLE IF EXISTS preventive_measures;")
        cursor.execute("DROP TABLE IF EXISTS disease_medications;")
        cursor.execute("DROP TABLE IF EXISTS medications;")
        cursor.execute("DROP TABLE IF EXISTS disease_symptoms;")
        cursor.execute("DROP TABLE IF EXISTS diseases;")
        cursor.execute("DROP TABLE IF EXISTS symptoms;")
        cursor.execute("DROP TABLE IF EXISTS doctor_specialists;")
        cursor.execute("DROP TABLE IF EXISTS patients;")
        conn.commit()
        init_db()

    # Check if database is already seeded
    cursor.execute("SELECT COUNT(*) FROM diseases;")
    if cursor.fetchone()[0] > 0 and not force_reseed:
        print("Database already seeded.")
        conn.close()
        return

    print("Seeding database with expanded clinical datasets, symptoms, diseases, medications & doctors...")

    # Define 24 Comprehensive Diseases
    diseases_data = [
        ("DIS_001", "Hypertension", "Cardiovascular", "Chronic elevation of systemic arterial blood pressure.", "I10"),
        ("DIS_002", "Type 2 Diabetes Mellitus", "Endocrine", "Metabolic disorder characterized by high blood sugar and insulin resistance.", "E11"),
        ("DIS_003", "Coronary Artery Disease", "Cardiovascular", "Impairment of blood flow through coronary arteries causing cardiac ischemia.", "I25.1"),
        ("DIS_004", "Asthma", "Respiratory", "Chronic inflammatory disease of the airways causing wheezing, breathlessness, and coughing.", "J45"),
        ("DIS_005", "Pneumonia", "Respiratory", "Infection that inflames air sacs in one or both lungs with sputum and high fever.", "J18.9"),
        ("DIS_006", "Gastroesophageal Reflux (GERD)", "Gastrointestinal", "Digestive disorder where acidic stomach contents irritate the esophagus lining.", "K21.9"),
        ("DIS_007", "Migraine", "Neurological", "Neurological disorder with recurrent throbbing headaches, nausea, and photophobia.", "G43.9"),
        ("DIS_008", "Rheumatoid Arthritis", "Orthopedic", "Autoimmune inflammatory condition causing painful joint swelling and erosion.", "M06.9"),
        ("DIS_009", "Chronic Kidney Disease", "Renal", "Gradual decline in renal filtration capacity and fluid-electrolyte retention.", "N18.9"),
        ("DIS_010", "Hyperthyroidism", "Endocrine", "Overproduction of thyroid hormones causing tachycardia, tremors, and heat intolerance.", "E05.9"),
        ("DIS_011", "Influenza (Flu)", "Infectious", "Acute contagious viral respiratory infection with high fever, chills, and myalgia.", "J11"),
        ("DIS_012", "Osteoarthritis", "Orthopedic", "Mechanical degeneration of joint cartilage and subchondral bone with morning stiffness.", "M19.9"),
        ("DIS_013", "Major Depressive Disorder", "Psychiatric", "Mental health disorder with persistent depressed mood, anhedonia, and fatigue.", "F32.9"),
        ("DIS_014", "Generalized Anxiety Disorder", "Psychiatric", "Excessive anxiety, muscle tension, tremors, and sleep disturbances.", "F41.1"),
        ("DIS_015", "Peptic Ulcer Disease", "Gastrointestinal", "Erosions in gastric or duodenal mucosa causing burning epigastric pain.", "K27.9"),
        ("DIS_016", "Iron Deficiency Anemia", "Hematological", "Deficiency of red blood cells/hemoglobin causing pallor, fatigue, and cold extremities.", "D50.9"),
        ("DIS_017", "Allergic Rhinitis", "Respiratory", "Allergen-triggered inflammation of nasal mucosa with sneezing, congestion, and watery eyes.", "J30.9"),
        ("DIS_018", "Chronic Obstructive Pulmonary Disease (COPD)", "Respiratory", "Persistent progressive airflow obstruction with chronic cough and dyspnea.", "J44.9"),
        ("DIS_019", "Eczema (Atopic Dermatitis)", "Dermatological", "Pruritic, dry, inflammatory skin condition with erythematous patches.", "L20.9"),
        ("DIS_020", "Urinary Tract Infection (UTI)", "Urological", "Bacterial infection of bladder/urethra with dysuria, urgency, and pelvic pain.", "N39.0"),
        ("DIS_021", "Common Cold (Viral Rhinitis)", "Infectious", "Mild viral upper respiratory tract infection with low-grade fever, sneezing, and runny nose.", "J00"),
        ("DIS_022", "Epistaxis & Acute Sinusitis", "ENT", "Nose bleeding associated with inflamed paranasal sinuses, facial pressure, and mucosal dryness.", "R04.0"),
        ("DIS_023", "Acute Gastroenteritis (Food Poisoning)", "Gastrointestinal", "Intestinal inflammation causing severe nausea, vomiting, watery diarrhea, and cramps.", "A09"),
        ("DIS_024", "Acute Bronchitis", "Respiratory", "Inflammation of bronchial bronchial tubes causing deep productive cough and chest congestion.", "J20.9")
    ]
    cursor.executemany("INSERT INTO diseases (code, name, category, description, icd10_code) VALUES (?, ?, ?, ?, ?);", diseases_data)

    # Define 53 Comprehensive Symptoms across 8 categories
    symptoms_data = [
        # Cardiovascular & Vitals
        ("SYM_001", "Chest Pain", "Cardiovascular", 1.9),
        ("SYM_002", "Shortness of Breath (Dyspnea)", "Respiratory", 1.8),
        ("SYM_003", "Elevated Blood Pressure", "Cardiovascular", 1.6),
        ("SYM_004", "Fatigue & Generalized Weakness", "General", 1.2),
        ("SYM_005", "Dizziness & Lightheadedness", "Neurological", 1.3),
        ("SYM_019", "Leg / Ankle Swelling (Edema)", "Cardiovascular", 1.6),
        ("SYM_021", "Rapid Heart Rate (Palpitations)", "Cardiovascular", 1.7),
        ("SYM_031", "Cold Hands & Feet", "Cardiovascular", 1.2),

        # Fever & Infectious Symptoms
        ("SYM_041", "Mild / Basic Fever (99-100.5°F)", "Fever & General", 1.3),
        ("SYM_011", "High Grade Fever (>101°F)", "Fever & General", 1.8),
        ("SYM_012", "Chills & Shivering", "Fever & General", 1.4),
        ("SYM_024", "Body Aches & Muscle Pain (Myalgia)", "Fever & General", 1.4),
        ("SYM_042", "Night Sweats", "Fever & General", 1.3),

        # ENT & Bleeding Symptoms
        ("SYM_043", "Nose Bleeding (Epistaxis)", "ENT & Respiratory", 1.7),
        ("SYM_025", "Sore Throat & Throat Irritation", "ENT & Respiratory", 1.3),
        ("SYM_026", "Runny Nose (Rhinorrhea)", "ENT & Respiratory", 1.1),
        ("SYM_027", "Frequent Sneezing", "ENT & Respiratory", 1.1),
        ("SYM_044", "Nasal Congestion / Blocked Nose", "ENT & Respiratory", 1.2),
        ("SYM_045", "Facial Pain / Sinus Pressure", "ENT & Respiratory", 1.4),
        ("SYM_046", "Loss of Smell / Taste", "ENT & Respiratory", 1.4),

        # Respiratory Symptoms
        ("SYM_009", "Persistent Dry Cough", "Respiratory", 1.4),
        ("SYM_047", "Productive Cough (Phlegm/Sputum)", "Respiratory", 1.5),
        ("SYM_010", "Wheezing / Whistling Breath", "Respiratory", 1.6),
        ("SYM_048", "Chest Tightness / Congestion", "Respiratory", 1.5),
        ("SYM_039", "Chronic Sputum Production", "Respiratory", 1.5),

        # Gastrointestinal Symptoms
        ("SYM_013", "Acid Reflux / Heartburn", "Gastrointestinal", 1.4),
        ("SYM_014", "Difficulty Swallowing (Dysphagia)", "Gastrointestinal", 1.5),
        ("SYM_020", "Nausea", "Gastrointestinal", 1.3),
        ("SYM_049", "Vomiting", "Gastrointestinal", 1.6),
        ("SYM_050", "Watery Diarrhea / Loose Stools", "Gastrointestinal", 1.6),
        ("SYM_028", "Abdominal Pain & Stomach Cramps", "Gastrointestinal", 1.5),
        ("SYM_029", "Bloating & Indigestion", "Gastrointestinal", 1.2),
        ("SYM_040", "Loss of Appetite", "Gastrointestinal", 1.2),

        # Neurological & Mental Health
        ("SYM_015", "Throbbing One-Sided Headache", "Neurological", 1.6),
        ("SYM_051", "Tension Headache / Head Heaviness", "Neurological", 1.3),
        ("SYM_016", "Sensitivity to Light & Sound", "Neurological", 1.4),
        ("SYM_022", "Hand Tremors / Shaking", "Neurological", 1.3),
        ("SYM_036", "Insomnia / Sleep Disturbance", "Psychiatric", 1.3),
        ("SYM_037", "Persistent Sadness / Low Mood", "Psychiatric", 1.5),
        ("SYM_038", "Excessive Worry / Nervousness", "Psychiatric", 1.4),

        # Endocrine & Metabolic
        ("SYM_006", "Frequent Urination (Polyuria)", "Endocrine & Renal", 1.5),
        ("SYM_007", "Excessive Thirst (Polydipsia)", "Endocrine & Renal", 1.5),
        ("SYM_008", "Unexplained Weight Loss", "Endocrine & General", 1.5),
        ("SYM_023", "Heat Intolerance & Excessive Sweating", "Endocrine", 1.4),

        # Orthopedic & Musculoskeletal
        ("SYM_017", "Joint Pain & Morning Stiffness", "Orthopedic", 1.5),
        ("SYM_018", "Joint Swelling, Warmth & Redness", "Orthopedic", 1.6),
        ("SYM_052", "Lower Back Pain", "Orthopedic", 1.3),

        # Dermatological & Urological
        ("SYM_030", "Pale Skin & Conjunctiva", "Hematological", 1.3),
        ("SYM_032", "Dry, Flaky, Itchy Skin", "Dermatological", 1.3),
        ("SYM_033", "Red Skin Rash / Eczematous Patches", "Dermatological", 1.4),
        ("SYM_053", "Yellowish Skin / Eyes (Jaundice)", "General", 1.8),
        ("SYM_034", "Burning Sensation During Urination", "Urological", 1.7),
        ("SYM_035", "Pelvic Discomfort / Cloudy Urine", "Urological", 1.5)
    ]
    cursor.executemany("INSERT INTO symptoms (code, name, category, severity_weight) VALUES (?, ?, ?, ?);", symptoms_data)

    disease_map = {row['code']: row['id'] for row in cursor.execute("SELECT id, code FROM diseases;").fetchall()}
    symptom_map = {row['code']: row['id'] for row in cursor.execute("SELECT id, code FROM symptoms;").fetchall()}

    # Disease-Symptom Links
    disease_symptom_links = [
        # Hypertension
        ("DIS_001", [("SYM_003", 2.0, 1), ("SYM_005", 1.3, 0), ("SYM_051", 1.4, 0), ("SYM_004", 1.1, 0), ("SYM_021", 1.2, 0)]),
        # Diabetes T2
        ("DIS_002", [("SYM_006", 2.2, 1), ("SYM_007", 2.2, 1), ("SYM_008", 1.5, 0), ("SYM_004", 1.4, 0), ("SYM_031", 1.1, 0)]),
        # CAD
        ("DIS_003", [("SYM_001", 2.5, 1), ("SYM_002", 2.0, 1), ("SYM_021", 1.6, 1), ("SYM_004", 1.3, 0), ("SYM_005", 1.2, 0), ("SYM_048", 1.5, 0)]),
        # Asthma
        ("DIS_004", [("SYM_010", 2.4, 1), ("SYM_002", 2.1, 1), ("SYM_048", 1.8, 1), ("SYM_009", 1.5, 0)]),
        # Pneumonia
        ("DIS_005", [("SYM_011", 2.2, 1), ("SYM_047", 2.1, 1), ("SYM_002", 1.9, 1), ("SYM_012", 1.6, 0), ("SYM_001", 1.4, 0), ("SYM_004", 1.3, 0)]),
        # GERD
        ("DIS_006", [("SYM_013", 2.4, 1), ("SYM_014", 1.5, 0), ("SYM_029", 1.4, 0), ("SYM_001", 1.2, 0), ("SYM_020", 1.2, 0)]),
        # Migraine
        ("DIS_007", [("SYM_015", 2.5, 1), ("SYM_016", 2.0, 1), ("SYM_020", 1.7, 1), ("SYM_005", 1.3, 0)]),
        # RA
        ("DIS_008", [("SYM_017", 2.3, 1), ("SYM_018", 2.2, 1), ("SYM_004", 1.4, 0), ("SYM_041", 1.1, 0)]),
        # CKD
        ("DIS_009", [("SYM_019", 2.2, 1), ("SYM_004", 1.8, 1), ("SYM_006", 1.5, 0), ("SYM_020", 1.3, 0), ("SYM_030", 1.2, 0)]),
        # Hyperthyroidism
        ("DIS_010", [("SYM_021", 2.0, 1), ("SYM_022", 1.8, 1), ("SYM_023", 1.8, 1), ("SYM_008", 1.5, 0), ("SYM_036", 1.3, 0)]),
        # Flu (Influenza)
        ("DIS_011", [("SYM_011", 2.2, 1), ("SYM_012", 2.0, 1), ("SYM_024", 2.0, 1), ("SYM_009", 1.6, 0), ("SYM_025", 1.4, 0), ("SYM_004", 1.6, 0)]),
        # Osteoarthritis
        ("DIS_012", [("SYM_017", 2.3, 1), ("SYM_018", 1.4, 0), ("SYM_052", 1.4, 0), ("SYM_004", 1.0, 0)]),
        # MDD
        ("DIS_013", [("SYM_037", 2.5, 1), ("SYM_004", 1.9, 1), ("SYM_036", 1.8, 0), ("SYM_040", 1.4, 0)]),
        # GAD
        ("DIS_014", [("SYM_038", 2.5, 1), ("SYM_021", 1.7, 0), ("SYM_036", 1.6, 0), ("SYM_022", 1.3, 0)]),
        # PUD
        ("DIS_015", [("SYM_028", 2.2, 1), ("SYM_013", 1.8, 1), ("SYM_020", 1.4, 0), ("SYM_040", 1.3, 0)]),
        # Anemia
        ("DIS_016", [("SYM_004", 2.3, 1), ("SYM_030", 2.2, 1), ("SYM_005", 1.6, 0), ("SYM_031", 1.6, 0), ("SYM_002", 1.3, 0)]),
        # Allergic Rhinitis
        ("DIS_017", [("SYM_027", 2.3, 1), ("SYM_026", 2.2, 1), ("SYM_044", 2.0, 1), ("SYM_025", 1.3, 0)]),
        # COPD
        ("DIS_018", [("SYM_002", 2.4, 1), ("SYM_047", 2.0, 1), ("SYM_039", 2.0, 1), ("SYM_010", 1.6, 0), ("SYM_048", 1.5, 0)]),
        # Eczema
        ("DIS_019", [("SYM_032", 2.4, 1), ("SYM_033", 2.2, 1)]),
        # UTI
        ("DIS_020", [("SYM_034", 2.5, 1), ("SYM_035", 2.2, 1), ("SYM_006", 1.7, 0), ("SYM_041", 1.2, 0)]),
        # Common Cold (Viral Rhinitis)
        ("DIS_021", [("SYM_041", 2.0, 1), ("SYM_026", 2.3, 1), ("SYM_027", 2.2, 1), ("SYM_025", 1.8, 1), ("SYM_044", 1.7, 0), ("SYM_009", 1.3, 0)]),
        # Epistaxis & Sinusitis
        ("DIS_022", [("SYM_043", 2.6, 1), ("SYM_044", 2.0, 1), ("SYM_045", 2.0, 1), ("SYM_051", 1.5, 0), ("SYM_041", 1.2, 0)]),
        # Acute Gastroenteritis (Food Poisoning)
        ("DIS_023", [("SYM_049", 2.5, 1), ("SYM_050", 2.5, 1), ("SYM_028", 2.2, 1), ("SYM_020", 2.0, 1), ("SYM_041", 1.3, 0), ("SYM_004", 1.4, 0)]),
        # Acute Bronchitis
        ("DIS_024", [("SYM_047", 2.3, 1), ("SYM_048", 2.0, 1), ("SYM_002", 1.8, 0), ("SYM_041", 1.4, 0), ("SYM_024", 1.3, 0)])
    ]

    for dis_code, sym_list in disease_symptom_links:
        dis_id = disease_map[dis_code]
        for sym_code, weight, is_primary in sym_list:
            if sym_code in symptom_map:
                sym_id = symptom_map[sym_code]
                cursor.execute("INSERT INTO disease_symptoms (disease_id, symptom_id, weight, is_primary) VALUES (?, ?, ?, ?);",
                               (dis_id, sym_id, weight, is_primary))

    # Define 32 Accurate Medications with specific directions
    medications_data = [
        # Antihypertensives & Cardiac
        ("Amlodipine 5mg", "Calcium Channel Blocker", "5mg once daily", "Take in the morning with water.", "Severe hypotension, aortic stenosis", "Peripheral edema, ankle swelling, flushing"),
        ("Telmisartan 40mg", "ARB Antihypertensive", "40mg once daily", "Take at the same time each morning.", "Pregnancy, severe biliary obstructive disorders", "Dizziness, back pain, sinus congestion"),
        ("Lisinopril 10mg", "ACE Inhibitor", "10mg once daily", "Take with or without meals.", "History of angioedema, pregnancy", "Dry tickly cough, hyperkalemia, headache"),
        ("Atorvastatin 20mg", "Statin / Lipid-lowering", "20mg once daily at bedtime", "Take at night for optimal cholesterol synthesis inhibition.", "Active hepatic disease, pregnancy", "Myalgia, dyspepsia, mild liver enzyme elevation"),
        ("Aspirin 75mg (Ecosprin)", "Antiplatelet", "75mg once daily after food", "Take with meals to prevent gastric irritation.", "Active peptic ulcer, bleeding disorders, aspirin allergy", "Gastric discomfort, heartburn, bruising"),

        # Antidiabetics
        ("Metformin 500mg Extended Release", "Biguanide / Antidiabetic", "500mg twice daily with main meals", "Take with food to minimize GI upset.", "Severe renal failure (eGFR < 30), metabolic acidosis", "Nausea, diarrhea, metallic taste"),
        ("Glimepiride 1mg", "Sulfonylurea", "1mg once daily before breakfast", "Must take with breakfast to prevent hypoglycemia.", "Sulfa allergy, severe renal/liver impairment", "Hypoglycemia, mild weight gain"),
        ("Insulin Glargine (Lantus)", "Long-acting Insulin", "10-14 units subcutaneous at bedtime", "Inject subQ at bedtime at rotating sites.", "Hypoglycemia episodes", "Hypoglycemia, injection site lipodystrophy"),

        # Antipyretics, Analgesics & Epistaxis
        ("Paracetamol (Acetaminophen) 650mg", "Antipyretic & Analgesic", "650mg every 6 hours as needed (Max 3g/day)", "Take after light food with plenty of water.", "Severe acute liver impairment", "Rare; well tolerated at therapeutic doses"),
        ("Ibuprofen 400mg", "NSAID Analgesic", "400mg twice daily after meals for 3-5 days", "Always take with food or antacid.", "Peptic ulcer, renal impairment, heart failure, asthma", "Stomach upset, heartburn, fluid retention"),
        ("Oxymetazoline 0.05% Nasal Spray", "Nasal Decongestant & Hemostatic", "1-2 sprays per nostril twice daily for max 3 days", "Tilt head forward slightly and spray; pinch nose 5 min.", "Uncontrolled hypertension, MAOIs, prolonged use > 3 days", "Rebound nasal congestion, stinging"),
        ("Tranexamic Acid 500mg", "Antifibrinolytic (Hemostatic)", "500mg three times daily for active bleeding", "Take with water during active bleeding episodes.", "Active thromboembolic disease, subarachnoid hemorrhage", "Nausea, diarrhea, mild headache"),

        # Respiratory & Allergy
        ("Salbutamol (Albuterol) Inhaler 100mcg", "Short-Acting Beta-2 Agonist", "2 puffs every 4-6 hours as needed for wheeze", "Shake inhaler well before use; rinse mouth.", "Tachyarrhythmias, severe hypersensitivity", "Fine finger tremors, tachycardia, palpitations"),
        ("Budesonide + Formoterol Inhaler (200/6mcg)", "Inhaled Corticosteroid + LABA", "1-2 puffs twice daily regularly", "Rinse mouth thoroughly with water after inhalation.", "Untreated systemic fungal/bacterial infections", "Oral thrush (candidiasis), hoarseness of voice"),
        ("Montelukast 10mg + Levocetirizine 5mg", "Antihistamine & Leukotriene Antagonist", "1 tablet once daily at bedtime", "Take at bedtime due to mild sedation.", "Severe renal impairment", "Drowsiness, dry mouth, headache"),
        ("Cetirizine 10mg", "Second-generation Antihistamine", "10mg once daily at night", "Take with water at bedtime.", "Severe renal dysfunction", "Mild drowsiness, dry mouth, fatigue"),
        ("Tiotropium 18mcg Rotacaps", "Long-Acting Anticholinergic", "1 rotacap inhalation once daily in morning", "Inhale via dry powder inhaler device.", "Narrow-angle glaucoma, severe urinary retention", "Dry mouth, throat irritation, urinary hesitation"),

        # Gastroenterology & Dehydration
        ("Pantoprazole 40mg", "Proton Pump Inhibitor (PPI)", "40mg once daily 30 minutes before breakfast", "Swallow whole with water on empty stomach.", "Hypersensitivity to substituted benzimidazoles", "Headache, diarrhea, abdominal pain"),
        ("Oral Rehydration Salts (ORS World Health Org Formula)", "Electrolyte Replacement", "Dissolve 1 sachet in 1 liter clean water; sip frequently", "Drink 200-400ml after each loose stool or vomiting.", "Intractable vomiting requiring IV, renal shutdown", "None when diluted correctly"),
        ("Ondansetron 4mg", "Antiemetic (5-HT3 Antagonist)", "4mg 30 minutes before meals as needed", "Place on tongue or swallow with sip of water.", "Congenital long QT syndrome, apomorphine use", "Headache, constipation, sensation of warmth"),
        ("Loperamide 2mg", "Antidiarrheal", "4mg initially, then 2mg after each loose stool (Max 8mg/day)", "Only use for non-infectious loose stools.", "Bloody diarrhea, high fever (>38.5°C), bacterial enteritis", "Abdominal cramps, constipation, nausea"),

        # Antibiotics & Anti-infectives
        ("Amoxicillin-Clavulanate 625mg (Augmentin)", "Penicillin-Class Antibiotic", "1 tablet twice daily for 7 days with meals", "Take at the start of a meal to optimize absorption.", "Penicillin allergy, amoxicillin-associated cholestatic jaundice", "Mild diarrhea, nausea, skin rash"),
        ("Azithromycin 500mg", "Macrolide Antibiotic", "500mg once daily for 3 days", "Take 1 hour before or 2 hours after meals.", "Hepatic impairment, QT prolongation", "Abdominal discomfort, diarrhea, nausea"),
        ("Ciprofloxacin 500mg", "Fluoroquinolone Antibiotic", "500mg twice daily for 5-7 days", "Drink plenty of water; avoid milk/antacids within 2 hrs.", "History of tendon disorders, myasthenia gravis, pregnancy", "Tendonitis risk, photosensitivity, nausea"),
        ("Nitrofurantoin 100mg Extended Release", "Urinary Antibacterial", "100mg twice daily for 5 days with food", "Take strictly with meals or milk.", "Severe renal impairment (eGFR < 45), glucose-6-PD deficiency", "Nausea, dark-tinted urine (harmless), headache"),
        ("Oseltamivir 75mg (Tamiflu)", "Neuraminidase Inhibitor Antiviral", "75mg twice daily for 5 days", "Begin within 48 hours of flu symptom onset with food.", "Severe hypersensitivity to oseltamivir", "Nausea, vomiting, insomnia"),

        # Neurological, Pain & Psychiatric
        ("Sumatriptan 50mg", "Selective 5-HT1 Receptor Agonist", "50mg at onset of migraine; may repeat in 2 hrs if needed (Max 200mg/day)", "Take immediately at first onset of migraine throbbing.", "Ischemic heart disease, uncontrolled hypertension, stroke history", "Chest tightness, tingling, flushing, drowsiness"),
        ("Meloxicam 15mg", "Selective COX-2 NSAID", "15mg once daily after main meal", "Take with food.", "Active gastrointestinal bleeding, severe renal failure", "Dyspepsia, GI ulcer risk, peripheral edema"),
        ("Methotrexate 15mg", "DMARD Immunosuppressant", "15mg once WEEKLY on specific day + Folic Acid 5mg next day", "Strictly once weekly; never take daily.", "Pregnancy, liver cirrhosis, severe bone marrow depression", "Mouth ulcers, nausea, elevated transaminases"),
        ("Escitalopram 10mg", "SSRI Antidepressant", "10mg once daily in the morning", "Take consistently each morning.", "Concurrent MAO inhibitors, congenital long QT", "Nausea, sleep disturbance, dry mouth"),
        ("Ferrous Ascorbate 100mg + Folic Acid", "Iron Supplement", "1 tablet once daily after lunch", "Take with citrus juice or water; avoid tea/coffee near dose.", "Hemochromatosis, active peptic ulcer", "Dark stools (normal), mild constipation"),
        ("Hydrocortisone 1% Topical Cream", "Topical Corticosteroid", "Apply thin layer to affected skin twice daily for 7 days", "Wash hands before and after applying; avoid eye contact.", "Untreated cutaneous viral/fungal infections", "Local skin thinning if overused, stinging")
    ]
    cursor.executemany("INSERT INTO medications (name, category, standard_dosage, timing_instructions, contraindications, side_effects) VALUES (?, ?, ?, ?, ?, ?);", medications_data)

    med_map = {row['name']: row['id'] for row in cursor.execute("SELECT id, name FROM medications;").fetchall()}

    # Map Diseases to specific medications
    disease_med_links = [
        ("DIS_001", [("Telmisartan 40mg", 1, 0.94), ("Amlodipine 5mg", 1, 0.92), ("Lisinopril 10mg", 2, 0.90)]),
        ("DIS_002", [("Metformin 500mg Extended Release", 1, 0.96), ("Glimepiride 1mg", 1, 0.91), ("Insulin Glargine (Lantus)", 2, 0.92)]),
        ("DIS_003", [("Atorvastatin 20mg", 1, 0.95), ("Aspirin 75mg (Ecosprin)", 1, 0.94), ("Telmisartan 40mg", 1, 0.91), ("Amlodipine 5mg", 2, 0.89)]),
        ("DIS_004", [("Salbutamol (Albuterol) Inhaler 100mcg", 1, 0.97), ("Budesonide + Formoterol Inhaler (200/6mcg)", 1, 0.95), ("Montelukast 10mg + Levocetirizine 5mg", 2, 0.88)]),
        ("DIS_005", [("Amoxicillin-Clavulanate 625mg (Augmentin)", 1, 0.93), ("Azithromycin 500mg", 1, 0.91), ("Paracetamol (Acetaminophen) 650mg", 1, 0.95)]),
        ("DIS_006", [("Pantoprazole 40mg", 1, 0.96)]),
        ("DIS_007", [("Sumatriptan 50mg", 1, 0.93), ("Ibuprofen 400mg", 1, 0.88), ("Paracetamol (Acetaminophen) 650mg", 2, 0.84)]),
        ("DIS_008", [("Methotrexate 15mg", 1, 0.92), ("Meloxicam 15mg", 1, 0.89)]),
        ("DIS_009", [("Telmisartan 40mg", 1, 0.92), ("Atorvastatin 20mg", 1, 0.89)]),
        ("DIS_010", [("Amlodipine 5mg", 2, 0.85)]),
        ("DIS_011", [("Oseltamivir 75mg (Tamiflu)", 1, 0.93), ("Paracetamol (Acetaminophen) 650mg", 1, 0.96), ("Cetirizine 10mg", 2, 0.85)]),
        ("DIS_012", [("Meloxicam 15mg", 1, 0.90), ("Paracetamol (Acetaminophen) 650mg", 1, 0.88)]),
        ("DIS_013", [("Escitalopram 10mg", 1, 0.94)]),
        ("DIS_014", [("Escitalopram 10mg", 1, 0.92)]),
        ("DIS_015", [("Pantoprazole 40mg", 1, 0.95), ("Amoxicillin-Clavulanate 625mg (Augmentin)", 2, 0.89)]),
        ("DIS_016", [("Ferrous Ascorbate 100mg + Folic Acid", 1, 0.97)]),
        ("DIS_017", [("Montelukast 10mg + Levocetirizine 5mg", 1, 0.95), ("Cetirizine 10mg", 1, 0.93)]),
        ("DIS_018", [("Tiotropium 18mcg Rotacaps", 1, 0.95), ("Salbutamol (Albuterol) Inhaler 100mcg", 1, 0.92), ("Budesonide + Formoterol Inhaler (200/6mcg)", 1, 0.91)]),
        ("DIS_019", [("Hydrocortisone 1% Topical Cream", 1, 0.94), ("Cetirizine 10mg", 1, 0.89)]),
        ("DIS_020", [("Nitrofurantoin 100mg Extended Release", 1, 0.95), ("Ciprofloxacin 500mg", 2, 0.90)]),
        ("DIS_021", [("Paracetamol (Acetaminophen) 650mg", 1, 0.96), ("Montelukast 10mg + Levocetirizine 5mg", 1, 0.93), ("Cetirizine 10mg", 2, 0.90)]),
        ("DIS_022", [("Oxymetazoline 0.05% Nasal Spray", 1, 0.96), ("Tranexamic Acid 500mg", 1, 0.92), ("Paracetamol (Acetaminophen) 650mg", 2, 0.88)]),
        ("DIS_023", [("Oral Rehydration Salts (ORS World Health Org Formula)", 1, 0.99), ("Ondansetron 4mg", 1, 0.94), ("Loperamide 2mg", 2, 0.86)]),
        ("DIS_024", [("Amoxicillin-Clavulanate 625mg (Augmentin)", 1, 0.91), ("Paracetamol (Acetaminophen) 650mg", 1, 0.94), ("Salbutamol (Albuterol) Inhaler 100mcg", 2, 0.89)])
    ]

    for dis_code, med_list in disease_med_links:
        dis_id = disease_map[dis_code]
        for med_name, line_tx, eff_score in med_list:
            if med_name in med_map:
                med_id = med_map[med_name]
                cursor.execute("INSERT INTO disease_medications (disease_id, medication_id, line_of_treatment, efficacy_score) VALUES (?, ?, ?, ?);",
                               (dis_id, med_id, line_tx, eff_score))

    # Preventive Measures
    preventive_data = [
        # Common Cold & Viral Rhinitis
        ("DIS_021", "Dietary", "Warm fluids, honey-ginger tea, chicken soup to soothe respiratory passages and stay hydrated.", "High"),
        ("DIS_021", "Lifestyle", "Adequate vocal and physical rest (7-8 hours sleep); steam inhalation twice daily.", "High"),
        ("DIS_021", "Screening", "Monitor body temperature every 6 hours; consult if fever persists beyond 3 days.", "Medium"),

        # Epistaxis & Sinusitis
        ("DIS_022", "Emergency", "Sit upright, lean forward slightly (do not lean back), and pinch soft part of nose firmly for 10-15 minutes.", "Critical"),
        ("DIS_022", "Lifestyle", "Apply nasal saline gel to prevent mucosal dryness; use bedroom cool-mist humidifier.", "High"),
        ("DIS_022", "Dietary", "Avoid picking nose, vigorous nose-blowing, hot/spicy foods, and aspirin during active bleeding episodes.", "High"),

        # Gastroenteritis
        ("DIS_023", "Dietary", "BRAT Diet (Bananas, Rice, Applesauce, Toast); strictly avoid dairy, caffeine, and oily foods.", "Critical"),
        ("DIS_023", "Lifestyle", "Immediate fluid replacement with ORS after every bowel movement to prevent acute hypovolemic dehydration.", "Critical"),

        # Bronchitis
        ("DIS_024", "Lifestyle", "Steam inhalation with eucalyptus oil; strictly avoid active and secondhand tobacco smoke.", "High"),

        # Hypertension
        ("DIS_001", "Dietary", "DASH Diet: Limit daily sodium intake to < 2,000 mg; increase potassium-rich bananas and greens.", "High"),
        ("DIS_001", "Lifestyle", "150 minutes of moderate aerobic activity weekly (brisk walking, cycling, swimming).", "High"),
        ("DIS_001", "Screening", "Home blood pressure monitoring twice weekly; annual cardiovascular checkup.", "Medium"),

        # Diabetes T2
        ("DIS_002", "Dietary", "Low Glycemic Index Diet: High fiber, legumes, whole grains; eliminate sugary beverages.", "High"),
        ("DIS_002", "Lifestyle", "Target 5-10% body weight reduction to markedly improve cellular insulin sensitivity.", "High"),
        ("DIS_002", "Screening", "Quarterly HbA1c testing (target < 7.0%); annual diabetic retinopathy and foot nerve screening.", "High"),

        # CAD
        ("DIS_003", "Dietary", "Mediterranean Diet rich in omega-3 fatty acids, extra virgin olive oil, walnuts, and wild fish.", "High"),
        ("DIS_003", "Lifestyle", "Complete smoking cessation; structured cardiac physical rehabilitation program.", "Critical"),
        ("DIS_003", "Screening", "Annual lipid profile screening, periodic stress echocardiogram or CT coronary angiogram.", "High"),

        # Asthma
        ("DIS_004", "Lifestyle", "Eliminate indoor allergens: Use HEPA air filters, wash beddings at 60°C, avoid pet dander.", "High"),
        ("DIS_004", "Vaccine", "Annual Influenza shot and Pneumococcal conjugate vaccination to prevent exacerbations.", "High"),

        # Pneumonia
        ("DIS_005", "Vaccine", "Pneumococcal Conjugate Vaccine (PCV20) and annual influenza immunization.", "Critical"),
        ("DIS_005", "Lifestyle", "Deep breathing exercises (incentive spirometry) and proper oral hygiene.", "High"),

        # GERD
        ("DIS_006", "Dietary", "Avoid late-night eating, citrus, chocolate, peppermint, coffee, and fried foods.", "High"),
        ("DIS_006", "Lifestyle", "Elevate head of bed by 6 inches; remain upright for at least 3 hours post meal.", "Medium"),

        # Migraine
        ("DIS_007", "Lifestyle", "Consistent sleep-wake cycle; stress reduction through progressive muscle relaxation.", "High"),
        ("DIS_007", "Dietary", "Maintain a headache food diary to eliminate triggers (aged cheeses, MSG, artificial sweeteners).", "Medium"),

        # RA
        ("DIS_008", "Lifestyle", "Hydrotherapy / gentle warm-water swimming to relieve joint stiffness without impact.", "High"),
        ("DIS_008", "Screening", "Quarterly Complete Blood Count, Liver Function Tests, and ESR/CRP inflammation tracking.", "High"),

        # CKD
        ("DIS_009", "Dietary", "Renal Diet: Restrict dietary sodium (<2g/day), phosphorus, and potassium as nephrologist directs.", "Critical"),
        ("DIS_009", "Screening", "Serum creatinine, eGFR, and spot urine albumin-to-creatinine ratio every 3-6 months.", "High"),

        # Flu
        ("DIS_011", "Vaccine", "Annual quadrivalent influenza vaccination.", "High"),
        ("DIS_011", "Lifestyle", "Frequent hand hygiene with 70% alcohol handrub or soap water for 20+ seconds.", "High"),

        # UTI
        ("DIS_020", "Dietary", "High fluid intake (> 2.5 to 3.0 Liters water/day); pure unsweetened cranberry juice.", "High"),
        ("DIS_020", "Lifestyle", "Urinate immediately post-intercourse; wipe from front to back to prevent bacterial transfer.", "High")
    ]

    for dis_code, m_type, desc, priority in preventive_data:
        if dis_code in disease_map:
            dis_id = disease_map[dis_code]
            cursor.execute("INSERT INTO preventive_measures (disease_id, measure_type, description, priority) VALUES (?, ?, ?, ?);",
                           (dis_id, m_type, desc, priority))

    # Define 12 Verified Doctor Specialists with rich profiles & Google Search links
    doctors_data = [
        ("Dr. Alexander Vance", "MBBS, MD (Cardiology), FACC", "Cardiology", "Metro General Heart Institute", 18, 4.9, 412, "$75 / ₹1,200", "Mon - Fri: 09:00 AM - 03:00 PM", "New York, NY", "+1 (555) 019-2451", "https://www.google.com/search?q=Dr+Alexander+Vance+Cardiologist+Metro+General", "Senior Interventional Cardiologist specializing in coronary artery disease, heart failure management, and preventive cardiac rehabilitation."),
        ("Dr. Elena Rostova", "MD, DM (Endocrinology), FACE", "Endocrinology", "St. Jude Diabetes & Endocrine Center", 14, 4.8, 298, "$65 / ₹1,000", "Mon - Sat: 10:00 AM - 04:00 PM", "Boston, MA", "+1 (555) 014-4822", "https://www.google.com/search?q=Dr+Elena+Rostova+Endocrinologist+St+Jude", "Renowned specialist in Type 2 Diabetes reversal, thyroid disorders, and metabolic syndrome risk reduction."),
        ("Dr. Marcus Chen", "MD, FCCP (Pulmonology)", "Pulmonology", "National Respiratory & Chest Institute", 20, 4.9, 520, "$80 / ₹1,300", "Tue - Sat: 08:30 AM - 02:30 PM", "Chicago, IL", "+1 (555) 018-8743", "https://www.google.com/search?q=Dr+Marcus+Chen+Pulmonologist+National+Respiratory", "Chief of Pulmonary Medicine, expert in chronic asthma, COPD, pneumonia complications, and pulmonary rehabilitation."),
        ("Dr. Sarah Jenkins", "MBBS, MD, FACG (Gastroenterology)", "Gastroenterology", "University Digestive Health Hospital", 13, 4.8, 345, "$70 / ₹1,100", "Mon - Fri: 11:00 AM - 05:00 PM", "San Francisco, CA", "+1 (555) 013-3904", "https://www.google.com/search?q=Dr+Sarah+Jenkins+Gastroenterologist+University+Digestive", "Clinical gastroenterologist focusing on GERD, peptic ulcer disease, acute gastroenteritis, and endoscopic procedures."),
        ("Dr. David Miller", "MD, FAAN (Neurology)", "Neurology", "Comprehensive Spine & Brain Institute", 22, 4.9, 610, "$90 / ₹1,500", "Mon - Thu: 09:00 AM - 01:00 PM", "Philadelphia, PA", "+1 (555) 017-7215", "https://www.google.com/search?q=Dr+David+Miller+Neurologist+Spine+Brain+Institute", "Senior Neurologist specializing in chronic migraine management, neurovascular conditions, and vertigo disorders."),
        ("Dr. Priya Sharma", "MBBS, MD, FACR (Rheumatology)", "Rheumatology", "Apex Joint & Arthritis Care Center", 15, 4.8, 275, "$65 / ₹1,000", "Mon - Sat: 10:00 AM - 03:00 PM", "Houston, TX", "+1 (555) 015-5638", "https://www.google.com/search?q=Dr+Priya+Sharma+Rheumatologist+Apex+Joint", "Expert in autoimmune arthritis, rheumatoid disease biologics, and joint pain preservation therapies."),
        ("Dr. Robert Taylor", "MD, FASN (Nephrology)", "Nephrology", "Kidney Health & Dialysis Specialists", 16, 4.8, 230, "$75 / ₹1,200", "Wed - Sun: 09:30 AM - 03:30 PM", "Seattle, WA", "+1 (555) 016-6491", "https://www.google.com/search?q=Dr+Robert+Taylor+Nephrologist+Kidney+Health", "Consultant Nephrologist dedicated to slowing chronic kidney disease progression and electrolyte balance."),
        ("Dr. Hannah Al-Mansoor", "MD (Psychiatry), FAPA", "Psychiatry", "MindCare Behavioral & Mental Health", 11, 4.7, 195, "$60 / ₹900", "Mon - Fri: 01:00 PM - 07:00 PM", "Austin, TX", "+1 (555) 012-2830", "https://www.google.com/search?q=Dr+Hannah+Al-Mansoor+Psychiatrist+MindCare", "Board-certified psychiatrist with extensive expertise in anxiety disorders, major depression, and holistic cognitive behavioral therapy."),
        ("Dr. James O'Connor", "MBBS, MD (Internal Medicine)", "Internal Medicine", "City Central Family Care & General Clinic", 19, 4.9, 780, "$50 / ₹800", "Mon - Sat: 08:00 AM - 08:00 PM", "Denver, CO", "+1 (555) 011-1927", "https://www.google.com/search?q=Dr+James+OConnor+Physician+City+Central", "Lead Primary Care Physician specialized in fever management, viral infections, preliminary CDSS diagnosis, and preventive screenings."),
        ("Dr. Sophia Martinez", "MD, FAAD (Dermatology)", "Dermatology", "Skin Health, Allergy & Laser Center", 13, 4.8, 385, "$65 / ₹1,000", "Tue - Sat: 10:00 AM - 04:00 PM", "Miami, FL", "+1 (555) 019-9402", "https://www.google.com/search?q=Dr+Sophia+Martinez+Dermatologist+Skin+Health", "Dermatology consultant specialized in atopic eczema, contact dermatitis, allergic rashes, and skin barrier repair."),
        ("Dr. Rajesh K. Gupta", "MS, DLO (ENT / Otolaryngology)", "ENT", "National Ear, Nose & Throat Center", 17, 4.9, 440, "$60 / ₹950", "Mon - Sat: 09:30 AM - 04:30 PM", "Chicago, IL", "+1 (555) 021-3982", "https://www.google.com/search?q=Dr+Rajesh+Gupta+ENT+Specialist+Nose+Bleeding", "Senior ENT Surgeon specialized in epistaxis (nose bleed) management, chronic sinusitis, allergy relief, and endoscopic nasal surgery."),
        ("Dr. Laura Bennett", "MD, FACS (Urology)", "Urology", "Premier Urology & Kidney Stone Institute", 15, 4.8, 310, "$70 / ₹1,150", "Mon - Fri: 09:00 AM - 03:00 PM", "Atlanta, GA", "+1 (555) 024-8819", "https://www.google.com/search?q=Dr+Laura+Bennett+Urologist+Premier+Urology", "Leading Urologist specializing in recurrent urinary tract infections (UTI), bladder health, and minimally invasive procedures.")
    ]
    cursor.executemany("""
        INSERT INTO doctor_specialists (name, qualifications, specialty, hospital, experience_years, rating, reviews_count, consultation_fee, timings, location, contact, google_query_url, bio)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    """, doctors_data)

    # Generate 1,000 Seed Patients with diagnoses
    first_names = ["James", "Mary", "John", "Patricia", "Robert", "Jennifer", "Michael", "Linda", "William", "Elizabeth",
                   "David", "Barbara", "Richard", "Susan", "Joseph", "Jessica", "Thomas", "Sarah", "Charles", "Karen",
                   "Christopher", "Nancy", "Daniel", "Lisa", "Matthew", "Betty", "Anthony", "Margaret", "Donald", "Sandra",
                   "Mark", "Ashley", "Paul", "Kimberly", "Steven", "Emily", "Andrew", "Donna", "Kenneth", "Michelle"]
    last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez",
                  "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin",
                  "Lee", "Perez", "Thompson", "White", "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson"]

    disease_list = list(disease_map.items()) # (code, id)
    disease_id_to_name = {row['id']: row['name'] for row in cursor.execute("SELECT id, name FROM diseases;").fetchall()}
    medical_conditions_pool = ["Hypertension", "Diabetes T2", "Hyperlipidemia", "Asthma", "GERD", "Osteoarthritis", "Migraine", "Chronic Sinusitis", "Penicillin Allergy", "None"]

    print("Generating 1,000 Seed Patients and Relational Treatment History...")
    patients_batch = []
    medical_hist_batch = []
    treatment_batch = []

    random.seed(42)

    for p_id in range(1, 1001):
        name = f"{random.choice(first_names)} {random.choice(last_names)}"
        age = random.randint(18, 85)
        gender = random.choice(["Male", "Female"])
        bmi = round(random.uniform(18.5, 38.5), 1)

        bp_sys = int(105 + (age * 0.3) + (bmi * 0.5) + random.randint(-10, 20))
        bp_dia = int(68 + (age * 0.15) + (bmi * 0.3) + random.randint(-5, 12))
        glucose = round(80.0 + (bmi * 1.2) + random.uniform(-10, 50), 1)
        cholesterol = round(160.0 + (age * 0.8) + (bmi * 1.5) + random.uniform(-20, 60), 1)

        smoking = random.choice(["Never", "Former", "Current"])
        activity = random.choice(["Sedentary", "Moderate", "Active"])

        # Determine risk category
        if bp_sys >= 140 or glucose >= 140 or cholesterol >= 240 or bmi >= 32:
            risk_cat = "High Risk"
        elif bp_sys >= 130 or glucose >= 110 or cholesterol >= 200 or bmi >= 27:
            risk_cat = "Moderate Risk"
        else:
            risk_cat = "Low Risk"

        dis_code, dis_id = random.choice(disease_list)
        diag_name = disease_id_to_name.get(dis_id, "Routine Health Exam")

        patients_batch.append((name, age, gender, bmi, bp_sys, bp_dia, glucose, cholesterol, smoking, activity, risk_cat, diag_name))

        # Add Medical History
        num_cond = random.choices([0, 1, 2], weights=[0.35, 0.45, 0.2])[0]
        if num_cond > 0:
            chosen_conds = random.sample(medical_conditions_pool[:-1], num_cond)
            for cond in chosen_conds:
                diag_year = random.randint(2018, 2026)
                medical_hist_batch.append((p_id, cond, f"{diag_year}-0{random.randint(1,9)}-15", "Routine clinical management"))

        # Add Treatment Records
        num_tx = random.randint(1, 2)
        for _ in range(num_tx):
            cur_meds = cursor.execute("SELECT medication_id FROM disease_medications WHERE disease_id = ?;", (dis_id,)).fetchall()
            if cur_meds:
                med_id = random.choice(cur_meds)[0]
                outcome = random.choices(["Recovered", "Improved", "No Change", "Adverse Reaction"], weights=[0.55, 0.35, 0.08, 0.02])[0]
                tx_date = f"{random.randint(2024, 2026)}-{random.randint(1,12):02d}-{random.randint(1,28):02d}"
                side_effect = "Mild nausea" if outcome == "Adverse Reaction" else "None"
                treatment_batch.append((p_id, dis_id, med_id, tx_date, outcome, side_effect))

    cursor.executemany("""
        INSERT INTO patients (name, age, gender, bmi, blood_pressure_sys, blood_pressure_dia, glucose_level, cholesterol, smoking_status, activity_level, risk_category, diagnosed_condition)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    """, patients_batch)

    cursor.executemany("""
        INSERT INTO medical_history (patient_id, condition_name, diagnosis_date, notes)
        VALUES (?, ?, ?, ?);
    """, medical_hist_batch)

    cursor.executemany("""
        INSERT INTO treatment_records (patient_id, disease_id, medication_id, treatment_date, outcome, side_effects_reported)
        VALUES (?, ?, ?, ?, ?, ?);
    """, treatment_batch)

    conn.commit()
    conn.close()
    print("Database successfully seeded with 1,000 patients, 53 symptoms, 24 diseases, 32 medications, and 12 doctors!")

if __name__ == '__main__':
    init_db()
    seed_database(force_reseed=True)
