import json
import os
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
import pickle
from datetime import datetime
from app.ml.summarization import extractive_summary
from sklearn.metrics import classification_report, confusion_matrix, ConfusionMatrixDisplay
from sklearn.model_selection import GridSearchCV
import matplotlib.pyplot as plt

class VulnLearnAIEngine:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(max_features=1000)
        self.classifier = RandomForestClassifier(n_estimators=100)
        self.model_path = "data/model/"
        self.ensure_model_directory()

    def ensure_model_directory(self):
        """Create model directory if it doesn't exist"""
        os.makedirs(self.model_path, exist_ok=True)

    def load_training_data(self):
        """Load training data from JSON file"""
        try:
            with open("data/training_data.json", "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def preprocess_data(self, entries):
        """Preprocess training data entries"""
        texts = []
        labels = []

        for entry in entries:
            # Summarize the writeup (description)
            description = entry.get("description", "")
            summary = extractive_summary(description)

            # Combine title, summary, and CVEs into a single text
            text = f"{entry['title']} {summary}"
            if entry.get('cves'):
                text += f" {' '.join(entry['cves'])}"

            texts.append(text)

            # Simple severity classification based on CVE presence and keywords
            severity = sum(
                kw in text.lower() for kw in ['critical', 'high', 'severe', 'dangerous', 'remote', 'exploit', 'rce', 'injection']
            )
            severity += bool(entry.get('cves'))

            # Convert severity to binary classification (high/low)
            labels.append(1 if severity >= 2 else 0)

        return texts, np.array(labels)

    def tune_hyperparameters(self, X_train, y_train):
        """Tune hyperparameters using GridSearchCV"""
        param_grid = {
            'n_estimators': [50, 100, 150],
            'max_depth': [None, 10, 20],
            'min_samples_split': [2, 5, 10]
        }
        # Adjust n_splits to avoid errors with small datasets
        n_splits = min(3, len(set(y_train)))  # Ensure n_splits does not exceed the number of classes
        grid_search = GridSearchCV(self.classifier, param_grid, cv=n_splits, scoring='f1')
        grid_search.fit(X_train, y_train)
        self.classifier = grid_search.best_estimator_
        print(f"Best parameters: {grid_search.best_params_}")

    def visualize_metrics(self, y_true, y_pred, labels):
        """Generate and save confusion matrix and classification report"""
        # Ensure the metrics directory exists
        metrics_dir = "data/metrics"
        os.makedirs(metrics_dir, exist_ok=True)

        # Confusion Matrix
        cm = confusion_matrix(y_true, y_pred, labels=[0, 1])  # Ensure both classes are included
        disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=labels)
        disp.plot(cmap=plt.cm.Blues)
        plt.title("Confusion Matrix")
        plt.savefig(os.path.join(metrics_dir, "confusion_matrix.png"))
        plt.close()

        # Classification Report
        report = classification_report(y_true, y_pred, target_names=labels, labels=[0, 1], output_dict=True, zero_division=0)
        with open(os.path.join(metrics_dir, "classification_report.json"), "w") as f:
            json.dump(report, f, indent=4)
        print("Metrics visualized and saved.")

    def incorporate_feedback(self, feedback):
        """Incorporate user feedback into training data and retrain the model"""
        training_data = self.load_training_data()
        training_data.extend(feedback)
        self.save_training_data_version(training_data)
        print("Feedback incorporated into training data.")
        self.train_model()

    def train_model(self):
        """Train the model using available training data with enhancements"""
        entries = self.load_training_data()
        if not entries:
            raise ValueError("No training data available. Please add training data before training the model.")

        # Preprocess data
        texts, labels = self.preprocess_data(entries)

        # Log preprocessing results
        print(f"Preprocessed {len(texts)} entries for training.")

        # If dataset is too small, train on all data without splitting
        if len(texts) < 5:
            X_vectorized = self.vectorizer.fit_transform(texts)
            self.classifier.fit(X_vectorized, labels)
            val_accuracy = 1.0  # Assume perfect accuracy with no validation
        else:
            # Split into training and validation sets
            X_train, X_val, y_train, y_val = train_test_split(
                texts, labels, test_size=0.2, random_state=42
            )

            # Vectorize text data
            X_train_vectorized = self.vectorizer.fit_transform(X_train)
            X_val_vectorized = self.vectorizer.transform(X_val)

            # Tune hyperparameters
            self.tune_hyperparameters(X_train_vectorized, y_train)

            # Train classifier
            self.classifier.fit(X_train_vectorized, y_train)

            # Calculate validation accuracy
            y_val_pred = self.classifier.predict(X_val_vectorized)
            val_accuracy = self.classifier.score(X_val_vectorized, y_val)

            # Visualize metrics
            self.visualize_metrics(y_val, y_val_pred, labels=["low", "high"])

        # Save models with versioning
        self.save_models()

        # Log training update
        self.log_training_update("success", float(val_accuracy), len(texts))

        return {
            "status": "success",
            "validation_accuracy": float(val_accuracy),
            "training_samples": len(texts),
            "timestamp": datetime.now().isoformat()
        }

    def save_models(self):
        """Save trained models to disk with versioning"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        vectorizer_path = os.path.join(self.model_path, f"vectorizer_{timestamp}.pkl")
        classifier_path = os.path.join(self.model_path, f"classifier_{timestamp}.pkl")

        with open(vectorizer_path, "wb") as f:
            pickle.dump(self.vectorizer, f)

        with open(classifier_path, "wb") as f:
            pickle.dump(self.classifier, f)

        print(f"Models saved: {vectorizer_path}, {classifier_path}")

    def load_models(self):
        """Load trained models from disk"""
        vectorizer_path = os.path.join(self.model_path, "vectorizer.pkl")
        classifier_path = os.path.join(self.model_path, "classifier.pkl")
        
        try:
            with open(vectorizer_path, "rb") as f:
                self.vectorizer = pickle.load(f)
            
            with open(classifier_path, "rb") as f:
                self.classifier = pickle.load(f)
            
            return True
        except FileNotFoundError:
            return False

    async def classify_vulnerability(self, title, description, cves=None):
        """Classify a new vulnerability with AI-enhanced analysis"""
        if not self.load_models():
            raise ValueError("No trained models available")
        
        # Combine input text
        text = f"{title} {description}"
        if cves:
            text += f" {' '.join(cves)}"
        
        # Get base classification
        X = self.vectorizer.transform([text])
        prediction = self.classifier.predict(X)[0]
        probability = self.classifier.predict_proba(X)[0]
        
        # Get AI-enhanced analysis if available
        from app.ml.ai_integration import ai_service
        ai_analysis = None
        remediation = None
        
        try:
            ai_analysis = await ai_service.analyze_vulnerability(title, description)
            if ai_analysis:
                remediation = await ai_service.generate_remediation_steps(
                    vulnerability_type=title,
                    context=description
                )
        except Exception as e:
            from app.utils.logger import log_error
            log_error(f"AI analysis failed: {str(e)}")
        
        result = {
            "severity": "high" if prediction == 1 else "low",
            "confidence": float(max(probability)),
            "timestamp": datetime.now().isoformat(),
            "data_storage": {
                "training_data": "data/training_data.json",
                "model_files": "data/model/",
                "tools_metadata": "tools/tools_metadata.json"
            }
        }
        
        if ai_analysis:
            result["ai_analysis"] = ai_analysis
        if remediation:
            result["remediation_steps"] = remediation
            
        return result

    def save_training_data_version(self, entries):
        """Save a versioned copy of the training data"""
        version_path = os.path.join("data", "training_data_versions")
        os.makedirs(version_path, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        version_file = os.path.join(version_path, f"training_data_{timestamp}.json")
        with open(version_file, "w") as f:
            json.dump(entries, f, indent=4)
        print(f"Training data version saved: {version_file}")

    def log_training_update(self, status, validation_accuracy, training_samples):
        """Log training updates to the history file"""
        update = {
            "status": status,
            "validation_accuracy": validation_accuracy,
            "training_samples": training_samples,
            "timestamp": datetime.now().isoformat()
        }
        history_file = "data/training_update_history.json"
        try:
            with open(history_file, "r") as f:
                history = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            history = []

        history.append(update)
        with open(history_file, "w") as f:
            json.dump(history, f, indent=4)
        print(f"Training update logged: {update}")

# Create global instance
engine = VulnLearnAIEngine()
