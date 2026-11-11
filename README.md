# Intelligent Healthcare Recommendation System using Data Mining Techniques

A comprehensive, publication-grade 7th-Semester Computer Science & Engineering Final-Year Project implementing an **Intelligent Healthcare Recommendation System and Clinical Decision Support System (CDSS)** powered by **Machine Learning, Data Mining Algorithms (Random Forest, KNN, Decision Tree, Naive Bayes, Apriori Association Mining, K-Means Clustering)**, and an integrated **Relational Database (SQLite)**.

---

## 📌 Executive Summary & Abstract

Modern clinical practice produces vast volumes of patient records, symptom presentations, and therapeutic responses. This project delivers an end-to-end Clinical Decision Support System (CDSS) designed to assist healthcare practitioners in preliminary disease diagnosis, emergency risk triage, medication dosage scheduling, contraindication cross-checking, and patient risk stratification.

The architecture integrates:
1. **Supervised Multi-Classifier Diagnostic Engine**: Evaluates active symptoms across 24 medical conditions with differential ranking and probability scores.
2. **Apriori Association Rule Mining**: Mines co-occurring symptom itemsets and clinical risk associations (`Support`, `Confidence`, `Lift`).
3. **Unsupervised K-Means Clustering**: Segments patient populations into 4 physiological risk clusters with 2D Principal Component Analysis (PCA) projection.
4. **Relational Database Management System (SQLite)**: Stores patient identity records, diagnostic logs, treatment histories, medication formularies, and specialist doctor directories.
5. **Verified Specialist Doctor Referral Engine**: Matches patient pathologies with verified specialists, consultation fees, clinic schedules, verified Google ratings, and Google search profile links.

---

## 🚀 Upgraded Key Features

### 1. Patient Identity Intake & Live Database Synchronization
- **Patient Full Name Field**: Clinicians or patients enter their name, demographics (age, gender), and vitals (BMI, blood pressure, glucose, cholesterol, smoking, activity level).
- **Automatic Relational Persistence**: When an AI diagnosis is executed, the entire clinical intake record is immediately inserted into the SQLite relational database (`patients`, `medical_history`, and `treatment_records` tables).
- **Live Database Explorer**: Newly evaluated patients immediately display at the top of the **Relational DB Explorer** table and can be queried using the built-in **SQL Analytical Sandbox**.

### 2. Expanded Symptoms & Medical History
- **53 Standardized Symptoms** across 8 medical categories:
  - *Fever & General*: Basic / Mild Fever, High Grade Fever, Chills & Shivering, Generalized Weakness, Night Sweats, Body Aches.
  - *ENT & Respiratory*: Nose Bleeding (Epistaxis), Sore Throat, Runny Nose, Sneezing, Blocked Nose, Sinus Pressure, Loss of Smell/Taste, Dry Cough, Wet/Productive Cough, Wheezing, Chest Tightness.
  - *Cardiovascular*: Chest Pain, Palpitations, Shortness of Breath, High BP, Cold Hands/Feet, Edema.
  - *Gastrointestinal*: Acid Reflux, Nausea, Vomiting, Watery Diarrhea, Abdominal Cramps, Bloating, Dysphagia, Loss of Appetite.
  - *Neurological & Mental*: One-Sided Throbbing Headache, Tension Headache, Dizziness, Light Sensitivity, Tremors, Insomnia, Anxiety, Low Mood.
  - *Endocrine & Renal*: Polyuria, Polydipsia, Weight Loss, Heat Intolerance.
  - *Orthopedic & Musculoskeletal*: Joint Pain, Morning Stiffness, Joint Swelling, Lower Back Pain.
  - *Dermatological & Urological*: Red Rashes, Dry/Itchy Skin, Jaundice, Burning Urination, Pelvic Discomfort.
- **Comprehensive Medical History & Allergies**:
  - Penicillin Allergy, Sulfa Drug Allergy, Aspirin/NSAID Sensitivity, Chronic Asthma, Hypertension, Type 2 Diabetes, Chronic Kidney Disease, Recurrent Epistaxis, Recurrent Fever, GERD, Chronic Sinusitis.

### 3. Accurate Condition-Specific & Symptom-Relief Medications
- **Dynamic Prescription Formulations**:
  - Automatically recommends primary disease medications (e.g. *Augmentin* for bacterial infection, *Pantoprazole* for GERD, *Amlodipine/Telmisartan* for hypertension, *Metformin* for diabetes).
  - Intelligently adds **symptom-directed supportive relief medications** (e.g., *Paracetamol 650mg* for fever, *Oxymetazoline 0.05% Nasal Spray & Tranexamic Acid* for nose bleeding, *ORS Electrolyte Solution* for dehydration/diarrhea, *Ondansetron* for nausea).
- **Dosage Guidelines & Timing Directions**: Detailed dosage, administration schedule (*"Take before breakfast"*, *"Take strictly with meals"*), and efficacy metrics.
- **Safety Contraindication Alerts**: Warns clinicians against prescribing penicillin to penicillin-allergic patients, NSAIDs to patients with kidney disease or asthma, etc.

### 4. Verified Specialist Doctors with Google Review Details
- **Google Verified Profile Integration**:
  - Displays doctor qualifications (e.g., *MBBS, MD - Cardiology, FACC*), hospital affiliation, clinical experience, consultation fee, and available timings.
  - Verified Google review rating (e.g., *4.9 ★ based on 412 Google reviews*).
  - **"Check Doctor Details"**: Opens a detailed doctor bio modal with clinic address and appointment simulation.
  - **"Open Doctor Profile on Google"**: Direct Google Search URL to inspect doctor credentials online.

### 5. "What-If" Digital Health Twin & 10-Year Prognostic Risk Simulator (Prescriptive Data Mining)
- **Multi-Variable Prognostic Regression Modeling**: Adapts Framingham and ACC/AHA cardiovascular and diabetic risk log-odds equations to forecast future clinical trajectories.
- **Interactive Biomarker Controls**: Real-time sliders for BMI, Systolic BP, Fasting Blood Glucose, Serum Cholesterol, Smoking status, and Physical Activity.
- **Biological Vascular Age vs Chronological Age**: Computes arterial stiffness differential (e.g. *Chronological: 45 yrs | Biological Heart Age: 58 yrs*).
- **10-Year Comparative Trajectory Curves**: Plots year-by-year compounding baseline risk against prescriptive intervention targets, demonstrating potential risk reduction (*e.g. -54.8% risk reduction and +5.4 healthy life-years gained*).

### 6. Printable Clinical Consultation Summary & PDF Export
- Generates a clinical consultation report featuring the patient's entered name, date, clinical triage alert, differential diagnosis, active symptoms, medications, preventive advice, and attending physician signature box.

---

## 🛠️ System Architecture & Technology Stack

- **Backend Framework**: Python 3.14, Flask, Flask-CORS
- **Machine Learning & Data Mining**: `scikit-learn`, `numpy`, `pandas`, `scipy`
- **Database Engine**: SQLite3 Relational Database Engine (`healthcare.db`)
- **Frontend Dashboard**: Glassmorphic HTML5, Custom Vanilla CSS3, JavaScript (ES6+), Chart.js
- **Typography & Icons**: Google Fonts (*Inter*, *Outfit*), FontAwesome 6 Pro Icons

```
d:\7 th sem project\
├── database/
│   ├── db_manager.py           # SQLite schema setup & 1,000 patient dataset seed script
│   └── healthcare.db           # Relational SQLite database
├── ml_engine/
│   ├── data_mining.py          # Supervised Classifiers, Apriori Mining, K-Means Clustering
│   ├── recommender.py          # CDSS Recommendation Engine & Safety Alerts
│   └── prognostic_simulator.py # "What-If" 10-Year Digital Health Twin Engine
├── static/
│   ├── css/
│   │   └── style.css           # Glassmorphic UI styling, slider controls & modals
│   └── js/
│       ├── app.js              # Frontend dashboard, patient persistence & simulator controller
│       └── charts.js           # Chart.js benchmarks, clusters, and trajectory curves
├── templates/
│   └── index.html              # 7-Tab Modern Single-Page Web Dashboard
├── app.py                      # Flask REST API Web Server
├── run.bat                     # Easy Launcher for Windows
└── README.md                   # Academic Project Documentation
```

---

## ⚡ How to Run the Project

### Prerequisites
- **Python 3.8+** (Tested on Python 3.14)
- **Required Packages**:
  ```bash
  pip install flask flask-cors scikit-learn numpy pandas
  ```

### Quick Start (Windows)
Double-click or run:
```cmd
run.bat
```

### Manual Terminal Execution
1. **Initialize and Seed the Relational Database**:
   ```bash
   python database/db_manager.py
   ```
2. **Start the Flask Web Application**:
   ```bash
   python app.py
   ```
3. **Open Dashboard**:
   Open your browser and navigate to:
   👉 `http://127.0.0.1:5000`

---

## 📊 Experimental Results & Machine Learning Benchmark

| Machine Learning Algorithm | Accuracy (%) | Precision (%) | Recall (%) | F1-Score (%) |
| :--- | :--- | :--- | :--- | :--- |
| **K-Nearest Neighbors (KNN)** | **93.47%** | **93.78%** | **93.47%** | **93.42%** |
| **Random Forest Classifier** | **90.27%** | **90.71%** | **90.27%** | **90.30%** |
| **Naive Bayes Classifier** | 60.53% | 67.07% | 60.53% | 59.62% |
| **Decision Tree Classifier** | 53.73% | 60.56% | 53.73% | 51.93% |

---

## 📜 Academic Project Information
- **Project Title**: Intelligent Healthcare Recommendation System Using Data Mining Techniques
- **Course**: 7th Semester B.Tech / B.E. Computer Science & Engineering Major Project
- **Domain**: Medical Informatics, Data Mining, Supervised Machine Learning, Clinical Decision Support Systems (CDSS)
