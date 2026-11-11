import sqlite3
import numpy as np
import pandas as pd
import os
import json
from sklearn.ensemble import RandomForestClassifier
from sklearn.naive_bayes import GaussianNB
from sklearn.tree import DecisionTreeClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from itertools import combinations
from collections import defaultdict

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'healthcare.db')

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

class DiseaseClassifier:
    """
    Supervised Multi-Model Classification Engine for Disease Diagnostic Prediction.
    Supports Random Forest, Naive Bayes, Decision Tree, and KNN.
    """
    def __init__(self):
        self.models = {
            'Random Forest': RandomForestClassifier(n_estimators=120, max_depth=12, random_state=42),
            'KNN': KNeighborsClassifier(n_neighbors=5, weights='distance'),
            'Decision Tree': DecisionTreeClassifier(max_depth=10, random_state=42),
            'Naive Bayes': GaussianNB()
        }
        self.symptom_cols = []
        self.disease_labels = []
        self.disease_id_to_name = {}
        self.disease_name_to_id = {}
        self.symptom_code_to_id = {}
        self.symptom_id_to_code = {}
        self.disease_symptom_weights = defaultdict(dict)
        self.is_trained = False
        self.benchmark_results = {}

    def prepare_training_dataset(self, num_samples=3000):
        conn = get_db()
        cursor = conn.cursor()

        # Load symptoms
        symptoms = cursor.execute("SELECT id, code, name FROM symptoms ORDER BY id;").fetchall()
        self.symptom_cols = [s['code'] for s in symptoms]
        self.symptom_code_to_id = {s['code']: s['id'] for s in symptoms}
        self.symptom_id_to_code = {s['id']: s['code'] for s in symptoms}

        # Load diseases
        diseases = cursor.execute("SELECT id, name FROM diseases ORDER BY id;").fetchall()
        self.disease_labels = [d['name'] for d in diseases]
        self.disease_id_to_name = {d['id']: d['name'] for d in diseases}
        self.disease_name_to_id = {d['name']: d['id'] for d in diseases}

        # Fetch disease-symptom links
        links = cursor.execute("SELECT disease_id, symptom_id, weight, is_primary FROM disease_symptoms;").fetchall()

        dis_sym_map = defaultdict(list)
        for link in links:
            s_code = self.symptom_id_to_code.get(link['symptom_id'])
            if s_code:
                dis_sym_map[link['disease_id']].append((s_code, link['weight'], link['is_primary']))
                self.disease_symptom_weights[link['disease_id']][s_code] = (link['weight'], link['is_primary'])

        conn.close()

        # Generate synthetic training samples
        X_data = []
        y_data = []

        np.random.seed(42)
        samples_per_disease = max(100, num_samples // len(diseases))

        for d_id, d_name in self.disease_id_to_name.items():
            sym_weights = dis_sym_map[d_id]
            if not sym_weights:
                continue

            for sample_idx in range(samples_per_disease):
                row = np.zeros(len(self.symptom_cols))
                
                # Full presentation vs partial presentation
                is_minimal_presentation = (sample_idx % 4 == 0)

                for sym_code, weight, is_primary in sym_weights:
                    idx = self.symptom_cols.index(sym_code)
                    if is_minimal_presentation:
                        prob = 0.95 if is_primary else 0.15
                    else:
                        prob = 0.88 if is_primary else min(0.60, 0.25 * weight)

                    if np.random.rand() < prob:
                        row[idx] = 1.0

                # Ensure at least one primary symptom is present
                primary_syms = [sc for sc, _, isp in sym_weights if isp]
                if primary_syms and sum(row) == 0:
                    chosen_p = np.random.choice(primary_syms)
                    row[self.symptom_cols.index(chosen_p)] = 1.0

                # Minimal background noise (2% chance)
                noise_mask = np.random.rand(len(self.symptom_cols)) < 0.02
                row = np.clip(row + noise_mask, 0, 1)

                X_data.append(row)
                y_data.append(d_name)

        return np.array(X_data), np.array(y_data)

    def train_and_evaluate(self):
        X, y = self.prepare_training_dataset()
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)

        self.benchmark_results = {}
        for name, model in self.models.items():
            model.fit(X_train, y_train)
            y_pred = model.predict(X_test)

            acc = float(accuracy_score(y_test, y_pred))
            prec = float(precision_score(y_test, y_pred, average='weighted', zero_division=0))
            rec = float(recall_score(y_test, y_pred, average='weighted', zero_division=0))
            f1 = float(f1_score(y_test, y_pred, average='weighted', zero_division=0))

            self.benchmark_results[name] = {
                'accuracy': round(acc * 100, 2),
                'precision': round(prec * 100, 2),
                'recall': round(rec * 100, 2),
                'f1_score': round(f1 * 100, 2)
            }

        self.is_trained = True
        return self.benchmark_results

    def predict_disease(self, active_symptoms):
        """
        Predict probable diseases based on active symptom codes.
        Combines Random Forest model probabilities with weighted domain matching for clinical realism.
        """
        if not self.is_trained:
            self.train_and_evaluate()

        # Build feature vector
        vector = np.zeros((1, len(self.symptom_cols)))
        for sym in active_symptoms:
            if sym in self.symptom_cols:
                idx = self.symptom_cols.index(sym)
                vector[0, idx] = 1.0

        rf_model = self.models['Random Forest']
        probabilities = rf_model.predict_proba(vector)[0]
        classes = rf_model.classes_

        # Calculate expert domain alignment scores
        domain_scores = {}
        active_set = set(active_symptoms)

        for d_id, d_name in self.disease_id_to_name.items():
            sym_dict = self.disease_symptom_weights.get(d_id, {})
            score = 0.0
            total_possible = 0.0
            for sym_code, (weight, is_primary) in sym_dict.items():
                w = weight * (2.0 if is_primary else 1.0)
                total_possible += w
                if sym_code in active_set:
                    score += w

            # Ratio of matched symptoms to active symptoms
            if total_possible > 0:
                match_ratio = score / total_possible
                domain_scores[d_name] = match_ratio

        # Ensemble hybrid prediction
        combined = []
        for cls_name, rf_prob in zip(classes, probabilities):
            cls_str = str(cls_name)
            d_score = domain_scores.get(cls_str, 0.0)
            
            # Blend RF statistical probability with clinical feature alignment
            blended_prob = (0.55 * rf_prob) + (0.45 * d_score)
            
            if blended_prob > 0.03:
                combined.append({
                    'disease': cls_str,
                    'raw_prob': blended_prob
                })

        # Normalize probabilities of top candidates to sum gracefully
        if not combined:
            return [{'disease': 'General Viral Syndrome', 'probability': 65.0}]

        combined.sort(key=lambda x: x['raw_prob'], reverse=True)
        top_candidates = combined[:5]
        total_p = sum(c['raw_prob'] for c in top_candidates)
        
        disease_predictions = []
        for c in top_candidates:
            pct = (c['raw_prob'] / total_p) * 100.0 if total_p > 0 else 20.0
            disease_predictions.append({
                'disease': c['disease'],
                'probability': round(float(pct), 1)
            })

        return disease_predictions


class AprioriRuleMiner:
    """
    Association Rule Mining Engine (Apriori Algorithm) for uncovering co-occurring symptom patterns.
    """
    def __init__(self, min_support=0.08, min_confidence=0.55):
        self.min_support = min_support
        self.min_confidence = min_confidence

    def fetch_transactions(self):
        conn = get_db()
        cursor = conn.cursor()
        diseases = cursor.execute("SELECT id, name FROM diseases;").fetchall()
        symptom_lookup = {row['id']: row['name'] for row in cursor.execute("SELECT id, name FROM symptoms;").fetchall()}

        transactions = []
        for dis in diseases:
            syms = cursor.execute("SELECT symptom_id FROM disease_symptoms WHERE disease_id = ?;", (dis['id'],)).fetchall()
            sym_names = [symptom_lookup[s['symptom_id']] for s in syms if s['symptom_id'] in symptom_lookup]
            for _ in range(20):
                transactions.append(sym_names)

        conn.close()
        return transactions

    def mine_rules(self):
        transactions = self.fetch_transactions()
        N = len(transactions)
        if N == 0:
            return []

        item_counts = defaultdict(int)
        for t in transactions:
            for item in set(t):
                item_counts[item] += 1

        frequent_1 = {frozenset([item]): count / N for item, count in item_counts.items() if (count / N) >= self.min_support}

        itemset_counts = defaultdict(int)
        for t in transactions:
            unique_items = sorted(list(set(t)))
            for pair in combinations(unique_items, 2):
                itemset_counts[frozenset(pair)] += 1

        frequent_2 = {pair: count / N for pair, count in itemset_counts.items() if (count / N) >= self.min_support}

        itemset3_counts = defaultdict(int)
        for t in transactions:
            unique_items = sorted(list(set(t)))
            for trio in combinations(unique_items, 3):
                itemset3_counts[frozenset(trio)] += 1

        frequent_3 = {trio: count / N for trio, count in itemset3_counts.items() if (count / N) >= self.min_support}

        all_frequent = {**frequent_1, **frequent_2, **frequent_3}

        rules = []
        for itemset, sup in all_frequent.items():
            if len(itemset) >= 2:
                for item in itemset:
                    antecedent = itemset - frozenset([item])
                    consequent = frozenset([item])
                    ant_sup = all_frequent.get(antecedent, 0)
                    if ant_sup > 0:
                        confidence = sup / ant_sup
                        con_sup = all_frequent.get(consequent, 0)
                        lift = confidence / con_sup if con_sup > 0 else 0

                        if confidence >= self.min_confidence:
                            rules.append({
                                'antecedent': list(antecedent),
                                'consequent': list(consequent),
                                'support': round(float(sup) * 100, 1),
                                'confidence': round(float(confidence) * 100, 1),
                                'lift': round(float(lift), 2)
                            })

        rules.sort(key=lambda x: x['lift'], reverse=True)
        return rules[:15]


class PatientClusterer:
    """
    Unsupervised Patient Segmentation Engine (K-Means Clustering).
    Clusters patients into health risk personas based on vital metrics.
    """
    def __init__(self, n_clusters=4):
        self.n_clusters = n_clusters
        self.scaler = StandardScaler()
        self.kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        self.pca = PCA(n_components=2, random_state=42)

    def cluster_patients(self):
        conn = get_db()
        df = pd.read_sql_query("""
            SELECT id, name, age, bmi, blood_pressure_sys, blood_pressure_dia, glucose_level, cholesterol, risk_category, diagnosed_condition
            FROM patients;
        """, conn)
        conn.close()

        if len(df) == 0:
            return {'cluster_summaries': [], 'points': []}

        features = ['age', 'bmi', 'blood_pressure_sys', 'glucose_level', 'cholesterol']
        X = df[features].values
        X_scaled = self.scaler.fit_transform(X)

        cluster_labels = self.kmeans.fit_predict(X_scaled)
        df['cluster'] = cluster_labels

        coords = self.pca.fit_transform(X_scaled)
        df['pca_x'] = coords[:, 0]
        df['pca_y'] = coords[:, 1]

        cluster_names = [
            "Cluster 0: Low Risk / Optimal Vitals",
            "Cluster 1: Metabolic Syndrome Risk",
            "Cluster 2: Cardiovascular Alert",
            "Cluster 3: Elderly Comorbidity Watch"
        ]

        cluster_summaries = []
        for k in range(self.n_clusters):
            cluster_df = df[df['cluster'] == k]
            if len(cluster_df) > 0:
                summary = {
                    'cluster_id': k,
                    'name': cluster_names[k],
                    'count': int(len(cluster_df)),
                    'avg_age': round(float(cluster_df['age'].mean()), 1),
                    'avg_bmi': round(float(cluster_df['bmi'].mean()), 1),
                    'avg_bp_sys': round(float(cluster_df['blood_pressure_sys'].mean()), 1),
                    'avg_glucose': round(float(cluster_df['glucose_level'].mean()), 1),
                    'avg_cholesterol': round(float(cluster_df['cholesterol'].mean()), 1)
                }
                cluster_summaries.append(summary)

        sample_points = df.sample(n=min(150, len(df)), random_state=42)
        visual_data = []
        for _, row in sample_points.iterrows():
            visual_data.append({
                'id': int(row['id']),
                'name': str(row['name']),
                'cluster': int(row['cluster']),
                'x': round(float(row['pca_x']), 3),
                'y': round(float(row['pca_y']), 3),
                'age': int(row['age']),
                'bmi': float(row['bmi']),
                'bp': int(row['blood_pressure_sys']),
                'glucose': float(row['glucose_level']),
                'cholesterol': float(row['cholesterol']),
                'condition': str(row.get('diagnosed_condition', 'Evaluated'))
            })

        return {
            'cluster_summaries': cluster_summaries,
            'points': visual_data
        }

if __name__ == '__main__':
    clf = DiseaseClassifier()
    bench = clf.train_and_evaluate()
    print("Benchmark Results:", bench)
    print("Test fever + cold:", clf.predict_disease(['SYM_041', 'SYM_026', 'SYM_027']))
    print("Test epistaxis:", clf.predict_disease(['SYM_043', 'SYM_044', 'SYM_045']))
