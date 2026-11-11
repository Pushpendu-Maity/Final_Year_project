from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import sqlite3
import os
import sys
from datetime import datetime

# Ensure parent directory is in sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.db_manager import DB_PATH, get_db_connection
from ml_engine.data_mining import DiseaseClassifier, AprioriRuleMiner, PatientClusterer
from ml_engine.recommender import CDSSRecommender
from ml_engine.prognostic_simulator import PrognosticRiskSimulator

app = Flask(__name__, template_folder='templates', static_folder='static')
CORS(app)

# Initialize ML Engines
recommender_engine = CDSSRecommender()
apriori_miner = AprioriRuleMiner()
patient_clusterer = PatientClusterer()
prognostic_simulator = PrognosticRiskSimulator()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/symptoms', methods=['GET'])
def get_symptoms():
    conn = get_db_connection()
    rows = conn.execute("SELECT id, code, name, category, severity_weight FROM symptoms ORDER BY category, name;").fetchall()
    conn.close()
    symptoms = [dict(row) for row in rows]
    return jsonify({'status': 'success', 'symptoms': symptoms})

@app.route('/api/diseases', methods=['GET'])
def get_diseases():
    conn = get_db_connection()
    rows = conn.execute("SELECT id, code, name, category, description, icd10_code FROM diseases ORDER BY name;").fetchall()
    conn.close()
    diseases = [dict(row) for row in rows]
    return jsonify({'status': 'success', 'diseases': diseases})

@app.route('/api/doctors', methods=['GET'])
def get_doctors():
    conn = get_db_connection()
    rows = conn.execute("""
        SELECT id, name, qualifications, specialty, hospital, experience_years, rating, reviews_count, consultation_fee, timings, location, contact, google_query_url, bio
        FROM doctor_specialists
        ORDER BY rating DESC;
    """).fetchall()
    conn.close()
    doctors = [dict(row) for row in rows]
    return jsonify({'status': 'success', 'doctors': doctors})

@app.route('/api/cdss/diagnose', methods=['POST'])
def run_cdss_diagnosis():
    data = request.json or {}
    active_symptoms = data.get('symptoms', [])
    vitals = data.get('vitals', {})
    medical_history = data.get('medical_history', [])
    patient_name = data.get('patient_name', '').strip() or "Anonymous Patient"

    if not active_symptoms:
        return jsonify({'status': 'error', 'message': 'Please select at least one symptom for preliminary diagnosis.'}), 400

    # 1. Run CDSS Recommendation Engine
    result = recommender_engine.generate_recommendations(active_symptoms, vitals, medical_history)

    # 2. Extract values for database insertion
    age = int(vitals.get('age', 45))
    gender = vitals.get('gender', 'Male')
    bmi = float(vitals.get('bmi', 24.5))
    bp_sys = int(vitals.get('bp_sys', 120))
    bp_dia = int(vitals.get('bp_dia', 80))
    glucose = float(vitals.get('glucose', 95.0))
    cholesterol = float(vitals.get('cholesterol', 180.0))
    smoking = vitals.get('smoking', 'Never')
    activity = vitals.get('activity', 'Moderate')
    
    # Calculate Risk Category
    if bp_sys >= 140 or glucose >= 140 or cholesterol >= 240 or bmi >= 32:
        risk_category = "High Risk"
    elif bp_sys >= 130 or glucose >= 110 or cholesterol >= 200 or bmi >= 27:
        risk_category = "Moderate Risk"
    else:
        risk_category = "Low Risk"

    primary_disease = result['diagnosis']['primary_disease']

    # 3. Store record in Relational Database (patients, medical_history, treatment_records)
    saved_patient_id = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Insert patient
        cursor.execute("""
            INSERT INTO patients (name, age, gender, bmi, blood_pressure_sys, blood_pressure_dia, glucose_level, cholesterol, smoking_status, activity_level, risk_category, diagnosed_condition)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, (patient_name, age, gender, bmi, bp_sys, bp_dia, glucose, cholesterol, smoking, activity, risk_category, primary_disease))
        
        saved_patient_id = cursor.lastrowid
        today_str = datetime.now().strftime("%Y-%m-%d")

        # Insert medical history
        for condition in medical_history:
            cursor.execute("""
                INSERT INTO medical_history (patient_id, condition_name, diagnosis_date, notes)
                VALUES (?, ?, ?, ?);
            """, (saved_patient_id, condition, today_str, "Recorded during CDSS Clinical Intake"))

        # Lookup disease ID
        disease_row = cursor.execute("SELECT id FROM diseases WHERE name = ?;", (primary_disease,)).fetchone()
        disease_id = disease_row['id'] if disease_row else 1

        # Insert treatment records for recommended medications
        for med in result.get('medications', []):
            med_id = med.get('id')
            if med_id:
                cursor.execute("""
                    INSERT INTO treatment_records (patient_id, disease_id, medication_id, treatment_date, outcome, side_effects_reported)
                    VALUES (?, ?, ?, ?, ?, ?);
                """, (saved_patient_id, disease_id, med_id, today_str, "Prescribed by CDSS", "None reported"))

        conn.commit()
        conn.close()
    except Exception as db_err:
        print(f"Warning: Failed to save patient record to DB: {db_err}")

    return jsonify({
        'status': 'success',
        'result': result,
        'saved_patient_id': saved_patient_id,
        'patient_name': patient_name,
        'risk_category': risk_category
    })

@app.route('/api/simulator/forecast', methods=['POST'])
def forecast_risk_trajectory():
    data = request.json or {}
    vitals = data.get('vitals', {})
    forecast = prognostic_simulator.calculate_risks(vitals)
    return jsonify({'status': 'success', 'forecast': forecast})

@app.route('/api/mining/apriori', methods=['GET'])
def get_apriori_rules():
    rules = apriori_miner.mine_rules()
    return jsonify({'status': 'success', 'count': len(rules), 'rules': rules})

@app.route('/api/mining/clusters', methods=['GET'])
def get_patient_clusters():
    cluster_data = patient_clusterer.cluster_patients()
    return jsonify({'status': 'success', 'data': cluster_data})

@app.route('/api/mining/benchmark', methods=['GET'])
def get_ml_benchmark():
    benchmark = recommender_engine.classifier.benchmark_results
    if not benchmark:
        benchmark = recommender_engine.classifier.train_and_evaluate()
    return jsonify({'status': 'success', 'benchmark': benchmark})

@app.route('/api/database/schema', methods=['GET'])
def get_db_schema():
    conn = get_db_connection()
    cursor = conn.cursor()

    tables = ['patients', 'symptoms', 'diseases', 'medications', 'preventive_measures', 'medical_history', 'treatment_records', 'doctor_specialists']
    schema = {}

    for table in tables:
        count = cursor.execute(f"SELECT COUNT(*) FROM {table};").fetchone()[0]
        columns = [col[1] for col in cursor.execute(f"PRAGMA table_info({table});").fetchall()]
        schema[table] = {
            'count': count,
            'columns': columns
        }

    conn.close()
    return jsonify({'status': 'success', 'schema': schema})

@app.route('/api/patients', methods=['GET'])
def get_patients():
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 15))
    search = request.args.get('search', '').strip()
    offset = (page - 1) * limit

    conn = get_db_connection()
    cursor = conn.cursor()

    if search:
        query = """
            SELECT * FROM patients 
            WHERE name LIKE ? OR risk_category LIKE ? OR diagnosed_condition LIKE ? 
            ORDER BY id DESC LIMIT ? OFFSET ?;
        """
        count_query = "SELECT COUNT(*) FROM patients WHERE name LIKE ? OR risk_category LIKE ? OR diagnosed_condition LIKE ?;"
        param = f"%{search}%"
        rows = cursor.execute(query, (param, param, param, limit, offset)).fetchall()
        total = cursor.execute(count_query, (param, param, param)).fetchone()[0]
    else:
        rows = cursor.execute("SELECT * FROM patients ORDER BY id DESC LIMIT ? OFFSET ?;", (limit, offset)).fetchall()
        total = cursor.execute("SELECT COUNT(*) FROM patients;").fetchone()[0]

    conn.close()
    patients = [dict(row) for row in rows]
    return jsonify({
        'status': 'success',
        'page': page,
        'limit': limit,
        'total': total,
        'patients': patients
    })

@app.route('/api/database/query', methods=['POST'])
def execute_custom_sql():
    data = request.json or {}
    sql = data.get('query', '').strip()

    if not sql:
        return jsonify({'status': 'error', 'message': 'Empty SQL query.'}), 400

    # Safety check: enforce read-only SELECT queries
    first_word = sql.split()[0].upper() if sql.split() else ''
    if first_word != 'SELECT':
        return jsonify({'status': 'error', 'message': 'Security Restricted: Only SELECT analytical queries are allowed.'}), 403

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(sql)
        rows = cursor.fetchall()
        cols = [description[0] for description in cursor.description] if cursor.description else []
        results = [dict(row) for row in rows[:100]]
        conn.close()
        return jsonify({'status': 'success', 'columns': cols, 'rows': results, 'total_rows': len(rows)})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 400

@app.route('/api/retrain', methods=['POST'])
def retrain_models():
    benchmark = recommender_engine.classifier.train_and_evaluate()
    return jsonify({'status': 'success', 'message': 'Machine Learning models retrained successfully!', 'benchmark': benchmark})

if __name__ == '__main__':
    print("Starting Intelligent Healthcare Recommendation System Web Server...")
    print("Dashboard available at: http://127.0.0.1:5000")
    app.run(host='127.0.0.1', port=5000, debug=True)
